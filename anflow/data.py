from __future__ import absolute_import

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shelve
import time



def generate_filename(params, prefix=None, suffix=None):
    """Generates the filename for the given parameters"""

    prefix = prefix or ""
    suffix = suffix or ""
    paramstring = "_".join(["{}{}".format(key, value)
                            for key, value in params.items()])
    return "{}{}{}".format(prefix, paramstring, suffix)

class FileWrapper(object):
    """Lazy file loading wrapper"""

    def __init__(self, filename, loader):
        """Constructor"""

        self.filename = filename
        self.loader = loader
        self.timestamp = os.path.getmtime(filename)

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

        filename = generate_filename(params, file_prefix, ".pkl")
        self._filename = filename
        self._params = set(params.keys())
        self._data = data
        self.timestamp = None

        for key, value in params.items():
            setattr(self, key, value)
    
    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
    
    def __setattr__(self, attr, value):
        non_params = ["params", "data", "timestamp"]
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
        self.timestamp = time.time()
        shelf['timestamp'] = self.timestamp
        shelf.close()

    @classmethod
    def load(cls, filename):
        """Lazy-loads the object from disk"""

        shelf = shelve.open(filename, protocol=2)
        params = shelf['params']
        timestamp = shelf['timestamp']
        shelf.close()

        new_datum = cls(params, None)
        delattr(new_datum, '_data')
        new_datum._filename = filename
        new_datum.timestamp = timestamp

        return new_datum

class DataSet(object):

    def __init__(self, params, prefix=None):
        """Constructor - initialize parameter set"""
        self._params = params
        self._prefix = prefix
    
    def filter(self, **kwargs):
        """Filter the dataset according to the supplied kwargs"""

        new_params = self._params[:]
        for key, value in kwargs.items():
            if key.endswith('__gt'):
                filter_func = lambda d: d[key[:-4]] > value
            elif key.endswith('__gte'):
                filter_func = lambda d: d[key[:-5]] >= value
            elif key.endswith('__lt'):
                filter_func = lambda d: d[key[:-4]] < value
            elif key.endswith('__lte'):
                filter_func = lambda d: d[key[:-5]] <= value
            elif key.endswith('__aprx'):
                abs_value = abs(value)
                def filter_func(d):
                    return abs(d[key[:-6]] - value) <= 1e-8 * abs_value
            else:
                filter_func = lambda d: d[key] == value

            new_params = filter(filter_func, new_params)
        return DataSet(new_params, self._prefix)

    def all(self):
        """Return a list of all Datum objects matched by the current
        parameters"""
        output = []
        for params in self._params:
            filename = generate_filename(params, self._prefix, '.pkl')
            output.append(Datum.load(filename))

        return output
