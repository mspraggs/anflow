from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle

from sqlalchemy import Column, String

from anflow.db.models import Model

class CachedData(Model):

    abstract = True
    hash = Column(String(32))

    @classmethod
    def from_object(cls, hash_object, value, central_value=None, error=None):
        """Create a cache datum, using the specified object to create the value
        for hash"""
        hash_value = cls.hashgen(hash_object)
        return cls(hash=hash_object, value=value, central_value=central_value,
                   error=error)

    @staticmethod
    def hashgen(hash_object):
        """Generate an md5 hash using the pickle value of the specified
        object"""
        pickle_value = pickle.dumps(hash_object, 2)
        return hashlib.md5(pickle_value).hexdigest()
