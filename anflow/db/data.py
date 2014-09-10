from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from anflow.conf import settings
from anflow.utils.debug import debug_message



class DataSet(object):

    def __init__(self, query, model_class):

        self.query = query.add_entity(model_class)
        self.model_class = model_class

    def all(self):
        return self.query.all()

    def filter(self, **kwargs):
        """Filter the data"""

        binops = []
        for key, value in kwargs.items():
            binops.append(getattr(self.model_class, key) == value)
        new_query = self.query.filter(*binops)
        return DataSet(new_query, self.model_class)

    def delete(self):
        self.query.delete()
