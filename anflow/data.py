from __future__ import absolute_import

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shelve



class FileWrapper(object):
    """Lazy file loading wrapper"""

    def __init__(self, filename, loader):
        """Constructor"""

        self.filename = filename
        self.loader = loader
        try:
            self.timestamp = os.path.getmtime(filename)
        except OSError:
            None

    @property
    def data(self):
        try:
            return self._data
        except AttributeError:
            self._data = self.loader(self.filename)
            return self._data

class Datum(object):
    """Holds a simulation result"""

    def __init__(self, params, data, file_prefix=None):
        """Constructor"""

        file_prefix = file_prefix or ""
        
        filename = (file_prefix
                    + "_".join(["{}{}".format(key, val)
                                for key, val in params.items()])
                    + ".pkl")
        self._filename = filename
        self._params = set(params.keys())
        self._data = data

        for key, value in params.items():
            setattr(self, key, value)
    
    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
    
    def __setattr__(self, attr, value):
        non_params = ["params", "data"]
        if not attr.startswith('_') and attr not in non_params:
            self._params.add(attr)
        return object.__setattr__(self, attr, value)

    @property
    def params(self):
        """Generate the dictionary of parameter values"""
        return dict([(key, getattr(self, key)) for key in self._params])

    @property
    def data(self):
        """Try to return the data if it's present, else load from disk"""
        try:
            return self._data
        except AttributeError:
            shelf = shelve.open(self._filename, protocol=2)
            self._data = shelf['data']
            shelf.close()
            return self._data

    def save(self):
        """Saves the datum to disk"""
        shelf = shelve.open(self._filename, protocol=2)
        shelf['params'] = self.params
        shelf['data'] = self.data
        shelf.close()

    @classmethod
    def load(cls, filename):
        """Lazy-loads the object from disk"""

        shelf = shelve.open(filename, protocol=2)
        params = shelf['params']
        shelf.close()

        new_datum = cls(params, None)
        delattr(new_datum, '_data')
        new_datum._filename = filename

        return new_datum

class DataSet(object):
    pass
