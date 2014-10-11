from __future__ import absolute_import
from __future__ import unicode_literals

import anydbm
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

    _extensions = ['', '.bak', '.dat', '.dir', '.pag', '.db']

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
            self._data = shelf[b'data']
            shelf.close()
            return self._data

    def save(self):
        """Saves the datum to disk"""
        shelf = shelve.open(self._filename, protocol=2)
        shelf[b'params'] = self.params
        shelf[b'data'] = self.data
        self.timestamp = time.time()
        shelf[b'timestamp'] = self.timestamp
        shelf.close()

    @classmethod
    def load(cls, filename):
        """Lazy-loads the object from disk"""

        shelf = shelve.open(filename, flag="r", protocol=2)
        params = shelf[b'params']
        timestamp = shelf[b'timestamp']
        shelf.close()

        new_datum = cls(params, None)
        delattr(new_datum, '_data')
        new_datum._filename = filename
        new_datum.timestamp = timestamp

        return new_datum

    def delete(self):
        """Deletes the datum file(s) on disk"""

        extensions = ['', '.bak', '.dat', '.dir', '.pag', '.db']
        for extension in extensions:
            try:
                os.unlink(self._filename + extension)
            except OSError:
                pass

class DataSet(object):

    def __init__(self, params, prefix=None):
        """Constructor - initialize parameter set"""
        self._params = params
        self._prefix = prefix

        self._counter = 0
    
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
            try:
                output.append(Datum.load(filename))
            except anydbm.error:
                raise IOError("Unable to open shelve file {}".format(filename))
        return output

    def first(self):
        """Return the first item in the DataSet"""
        try:
            filename = generate_filename(self._params[0], self._prefix, '.pkl')
        except IndexError:
            return
        try:
            return Datum.load(filename)
        except anydbm.error:
            raise IOError("Unable to open shelve file {}".format(filename))

    def __iter__(self):
        """Return the iterator for the dataset"""
        return self

    def next(self):
        """Next function for iterating"""
        if self._counter >= len(self._params):
            self._counter = 0
            raise StopIteration
        else:
            filename = generate_filename(self._params[self._counter],
                                         self._prefix, '.pkl')
            self._counter += 1
            return Datum.load(filename)
            
