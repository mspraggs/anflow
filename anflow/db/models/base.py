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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from anflow.conf import settings
from anflow.db.data import DataSet
from anflow.db.models.manager import Manager
from anflow.utils.debug import debug_message
from anflow.utils import get_study
from anflow.utils.logging import Log
from anflow.utils.io import projectify



Base = declarative_base()

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
    results_format = None # The template for the model filename
    depends_on = None # A list of models this model depends on
    resampler = None # The resampler object that'll do the resampling

    id = Column(Integer, primary_key=True)
    model_name = Column(String(40))

    value = Column(PickleType)
    central_value = Column(PickleType)
    error = Column(PickleType)

    time_saved = Column(DateTime, default=datetime.datetime.now)

    def __init__(self):
        """Set up empty results list"""

        self.mainargspec = inspect.getargspec(self.main)
        if not self.results_format:
            try:
                self.results_format = self.input_stream.path_format
            except AttributeError as e:
                debug_message(e)
                raise AttributeError("Member results_format not specified and "
                                     "input_stream has no member path_format")

        self.study_name = get_study(self.__module__)

    @classproperty
    @classmethod
    def data(cls):
        return Manager(cls)

    def run(self, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        for datum in self.input_stream:
            # Convert parsed to types indicated by parameters
            for key in datum.paramsdict().keys():
                param_type = getattr(self, key)
                setattr(datum, key, param_type(getattr(datum, key)))
            # Combine parameters
            all_params = dict(zip(self.mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(datum.paramsdict())
            main_partial = partial(Log("Running model function {}.main"
                                       .format(self.__class__.__name__))
                                   (self.main),
                                   **all_params)

            if self.resampler:
                results = self.resampler(datum, main_partial)
                result = results[0]
                centre = results[1]
                try:
                    error = results[2]
                except IndexError as e:
                    debug_message(e)
            else:
                result = main_partial(datum.value)
                
            filename = os.path.join(settings.RESULTS_TEMPLATE
                                    .format(study_name=self.study_name),
                                    self.results_format.format(**all_params))
            new_datum = Datum(all_params, result, projectify(filename))
            try:
                new_datum.central_value = centre
                new_datum.error = error
            except NameError as e:
                debug_message(e)

            self.new_results.append(new_datum)

    def save(self):
        """Saves the result defined by the specified parameters"""
        engine = create_engine(settings.DB_PATH)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        session.add(self)
        session.commit()

    def paramsdict(self):

        excluded_names = ['value', 'central_value', 'error']
        out = {}

        for name in dir(self):
            member = getattr(self, name)
            if isinstance(member, Column) and name not in excluded_names:
                out.update(dict(name=member))
        return out
