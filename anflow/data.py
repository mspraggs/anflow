from __future__ import absolute_import
from __future__ import unicode_literals

import anydbm
import operator
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shelve
import time



def generate_filename(params, prefix=None, suffix=None, path_template=None):
    """Generates the filename for the given parameters"""

    if path_template:
        return path_template.format(**params)
    else:
        prefix = prefix or ""
        suffix = suffix or ""
        sorted_items = sorted(params.items(), key=lambda item: item[0])
        paramstring = "_".join(["{}{}".format(key, value)
                                for key, value in sorted_items])
        return "{}{}{}".format(prefix, paramstring, suffix)


def _aprx(x, y, rtol, atol):
    """Simple approximate operator"""
    return abs(x - y) <= rtol * abs(y) + atol


class FileWrapper(object):
    """Lazy file loading wrapper"""

    def __init__(self, filename, loader, timestamp=None):
        """Constructor"""

        self.filename = filename
        self.loader = loader
        self.timestamp = timestamp or os.path.getmtime(filename)

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

    def __init__(self, params, data, file_prefix=None, path_template=None):
        """Constructor"""

        filename = generate_filename(params, file_prefix, ".pkl", path_template)
        self.filename = filename
        self._params = set(params.keys())
        self._data = data
        self.timestamp = None

        for key, value in params.items():
            setattr(self, key, value)
    
    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
    
    def __setattr__(self, attr, value):
        non_params = ["params", "data", "timestamp", "filename"]
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
            shelf = shelve.open(self.filename, protocol=2)
            self._data = shelf[b'data']
            shelf.close()
            return self._data

    def save(self):
        """Saves the datum to disk"""
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))
        shelf = shelve.open(self.filename, protocol=2)
        shelf[b'params'] = self.params
        shelf[b'data'] = self.data
        self.timestamp = time.time()
        shelf[b'timestamp'] = self.timestamp
        shelf.close()

    @classmethod
    def load(cls, filename):
        """Lazy-loads the object from disk"""

        try:
            shelf = shelve.open(filename, flag="r", protocol=2)
        except anydbm.error:
            return None
        params = shelf[b'params']
        timestamp = shelf[b'timestamp']
        shelf.close()

        new_datum = cls(params, None)
        delattr(new_datum, '_data')
        new_datum.filename = filename
        new_datum.timestamp = timestamp

        return new_datum

    def delete(self):
        """Deletes the datum file(s) on disk"""

        for extension in self._extensions:
            try:
                os.unlink(self.filename + extension)
            except OSError:
                pass

class DataSet(object):

    def __init__(self, params, config, prefix=None, path_template=None):
        """Constructor - initialize parameter set"""
        self.config = config
        self._params = params
        self._prefix = prefix
        self._template = path_template

        self._counter = 0
    
    def filter(self, *args, **kwargs):
        """Filter the dataset according to the supplied kwargs"""

        query = Query(*args, **kwargs)
        return DataSet(query.evaluate(self._params), self.config, self._prefix,
                       self._template)

    def all(self):
        """Return a list of all Datum objects matched by the current
        parameters"""
        output = []
        actual_prefix = os.path.join(self.config.RESULTS_DIR, self._prefix)
        for params in self._params:
            filename = generate_filename(params, actual_prefix, '.pkl',
                                         self._template)
            datum = Datum.load(filename)
            if datum is not None:
                output.append(datum)
        return output

    def first(self):
        """Return the first item in the DataSet"""
        actual_prefix = os.path.join(self.config.RESULTS_DIR, self._prefix)
        try:
            filename = generate_filename(self._params[0], actual_prefix, '.pkl',
                                         self._template)
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
            datum = None
            while datum is None and self._counter < len(self._params):
                actual_prefix = os.path.join(self.config.RESULTS_DIR, self._prefix)
                filename = generate_filename(self._params[self._counter],
                                             actual_prefix, '.pkl', self._template)
                self._counter += 1
                datum = Datum.load(filename)
            return datum

    def __len__(self):
        return len(self._params)


class Query(object):
    """Parameter filtering class using tree/node structure"""

    comparison_map = {'gt': operator.gt,
                      'gte': operator.ge,
                      'lt': operator.lt,
                      'lte': operator.le,
                      'aprx': lambda x, y: _aprx(x, y, 1e-5, 1e-8)}

    def __init__(self, *args, **kwargs):
        """Query Constructor"""
        self.children = []
        for arg in args:
            if not isinstance(arg, type(arg)):
                raise TypeError("Invalid argument {} to with type {} passed "
                                "to {} constructor".format(arg, type(arg),
                                                           self.__class__
                                                           .__name__))
            self.children.append(arg)

        for key, value in kwargs.items():
            key_split = key.split('__')
            child = type(self)()
            op = (
                self.comparison_map[key_split[-1]]
                if len(key_split) > 1 else operator.eq
            )
            child._set_filter(op, key_split[0], value)
            self.children.append(child)

        self.connector = operator.and_
        self.filter_func = None
        self.negate = False

    def _set_filter(self, func, parameter_name, parameter_value):
        """Specify a filter function that returns True or False for a given
        parameter value"""
        self.filter_func = lambda d: func(d[parameter_name], parameter_value)

    def _recurse(self, parameters):
        """Recursively call _recurse on children to build up a list of True
        and False statements"""

        if self.filter_func:
            results = map(self.filter_func, parameters)
        else:
            results = [child._recurse(parameters) for child in self.children]
            results = [reduce(self.connector, result)
                       for result in zip(*results)]
        return [not result if self.negate else result for result in results]

    def evaluate(self, parameters):
        """Evaluate which parameters we're keeping and which we're discarding,
        returning the list of parameter combinations that we do want to keep"""

        results = self._recurse(parameters)
        return [params for keep, params in zip(results, parameters)
                if keep]

    def __and__(self, other):
        """And operator"""
        out = type(self)(self, other)
        out.connector = operator.and_
        return out

    def __or__(self, other):
        """Or operator"""
        out = type(self)(self, other)
        out.connector = operator.or_
        return out

    def __invert__(self):
        """Not operator"""
        ret = type(self)(*self.children)
        ret.negate = not self.negate
        return ret