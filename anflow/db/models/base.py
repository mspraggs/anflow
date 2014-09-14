from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect
import re
from functools import partial
import datetime

from sqlalchemy import (create_engine, Column, DateTime,
                        Integer, String, PickleType)
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import QueryableAttribute

from anflow.conf import settings
from anflow.db import Base
from anflow.db.data import DataSet
from anflow.db.models.manager import Manager
from anflow.utils.debug import debug_message
from anflow.utils import get_study
from anflow.utils.logging import Log
from anflow.utils.io import projectify



class MetaModel(DeclarativeMeta):
    # Meta class to create static data member for Model
    def __new__(cls, names, bases, attrs):
        try:
            attrs['abstract']
        except KeyError as e:
            debug_message(e)
            attrs['abstract'] = False
            
        new_class = super(MetaModel, cls).__new__(cls, names, bases, attrs)
        tablename = "table_{}".format(new_class.__name__)

        if names == "Model":
            new_class.__tablename__ = tablename
            new_class.__mapper_args__ = {'polymorphic_on': new_class.model_name}
        else:
            new_class.__mapper_args__ = {'polymorphic_identity': tablename}

        new_class._params = []
        excluded_names = ['value', 'central_value', 'data', 'error', 'id',
                          'model_name', 'timestamp']
        for name in dir(new_class):
            if name in excluded_names:
                continue
            if isinstance(getattr(new_class, name),
                          (Column, QueryableAttribute)):
                new_class._params.append(name)
        return new_class

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

class Model(Base):

    __metaclass__ = MetaModel

    abstract = False
    main = None # The function that encapsulates the model behaviour
    input_stream = None # The raw data to feed into the model
    parameters = None # A list of additional parameters to feed the model
    depends_on = None # A list of models this model depends on
    resampler = None # The resampler object that'll do the resampling

    id = Column(Integer, primary_key=True)
    model_name = Column(String(40))

    value = Column(PickleType)
    central_value = Column(PickleType)
    error = Column(PickleType)

    timestamp = Column(DateTime, default=datetime.datetime.now)

    @classproperty
    @classmethod
    def data(cls):
        return Manager(cls)

    @classmethod
    def run(cls, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        mainargspec = inspect.getargspec(cls.main)
        results = []
        study_name = get_study(cls.__module__)

        for datum in cls.input_stream:
            # Combine parameters
            all_params = dict(zip(mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(datum.paramsdict())
            main_partial = partial(Log("Running model function {}.main"
                                       .format(cls.__class__.__name__))
                                   (cls.main), **all_params)

            if cls.resampler:
                result, centre, error = cls.resampler(datum, main_partial)
                results.append(cls(value=result, central_value=centre,
                                   error=error, **all_params))
            else:
                result = main_partial(datum.value)
                results.append(cls(value=result, **all_params))

        return results

    def save(self):
        """Saves the result defined by the specified parameters"""
        engine = create_engine(settings.DB_PATH)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        session.add(self)
        session.commit()

    def paramsdict(self):
        out = {}
        for name in self._params:
            out.update({name: getattr(self, name)})
        return out
