from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from anflow.utils.debug import debug_message



class Datum(object):

    def __init__(self, params, data, filename=None):

        for key, value in params.items():
            setattr(self, key, value)

        self.value = data
        self._filename = filename
        self._params = params

    def paramsdict(self):
        return self._params

    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
        
    def __setattr__(self, attr, value):
        return object.__setattr__(self, attr, value)

    def delete(self):
        os.unlink(self._filename)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._filename))
        except OSError as e:
            debug_message(e)

        with open(self._filename, 'w') as f:
            pickle.dump((self.paramsdict(), self.value), f)

    @classmethod
    def load(cls, filename):
        with open(filename) as f:
            params, data = pickle.load(f)
        return cls(params, data, filename)

class DataSet(list):

    def __init__(self, *args):
        list.__init__(self, *args)

    def filter(self, **kwargs):
        """Filter the data"""

        out = self
        for key, value in kwargs.items():
            def filter_function(datum):
                return getattr(datum, key) == value
            out = filter(filter_function, out)
        return DataSet(out)

    def delete(self):

        size = len(self)
        for i in range(size):
            item = self.pop(-1)
            item.delete()

    def save(self):
        for datum in self:
            datum.save()
        
    def __repr__(self):
        return object.__repr__(self)

    def __contains__(self, testdatum):
        return testdatum._filename in [datum._filename for datum in self]
