from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
from functools import partial
import inspect
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import re
import sys

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        PickleType)
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm import backref, deferred, relationship
from sqlalchemy.orm.attributes import QueryableAttribute

from anflow.conf import settings
from anflow.db import Base
from anflow.db.models.manager import Manager
from anflow.utils.debug import debug_message
from anflow.utils import get_study
from anflow.utils.logging import Log, logger
from anflow.utils.io import projectify



class MetaModel(DeclarativeMeta):
    # Meta class to create static data member for Model
    def __new__(cls, names, bases, attrs):
        try:
            attrs['abstract']
        except KeyError as e:
            attrs['abstract'] = False
            
        new_class = super(MetaModel, cls).__new__(cls, names, bases, attrs)
        tablename = "anflow{}".format(new_class.__name__)

        new_class.__tablename__ = tablename
        if names == "BaseModel":
            new_class.__mapper_args__ = {'polymorphic_on': new_class.model_name}
        else:
            for base in bases:
                if issubclass(base, Base):
                    foreign_key_name = "anflow{}.id".format(base.__name__)
                    break
            new_class.__mapper_args__ = {'polymorphic_identity': tablename}
            new_class.id = Column(Integer, ForeignKey(foreign_key_name),
                                  primary_key=True)

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

class BaseModel(Base):

    __metaclass__ = MetaModel

    id = Column(Integer, primary_key=True)
    model_name = Column(String(40))
    
    @classproperty
    @classmethod
    def data(cls):
        return Manager(cls)

    def save(self):
        """Saves the result defined by the specified parameters"""

        size = 0
        for value in self.paramsdict().values():
            size += sys.getsizeof(value)
        for item in [self.value, self.central_value, self.error]:
            size += len(pickle.dumps(item))
        log = logger()
        log.info("Saving {} bytes, {} MB".format(size, size / 1024**2))

        settings.session.add(self)
        settings.session.commit()
