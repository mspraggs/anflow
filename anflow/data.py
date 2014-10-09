from __future__ import absolute_import

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle



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

    def __init__(self, params, data, file_prefix=None, saver=None):
        """Constructor"""
        if not saver:
            def saver(filename, obj):
                with open(filename, 'w') as f:
                    pickle.dump(obj, f)
            extension = ".pkl"
        else:
            extension = ""
        self._saver = saver
        
        filename = (file_prefix
                    + "_".join(["{}{}".format(key, val)
                                for key, val in params.items()])
                    + extension)
        self._filename = filename
        self._params = set(params.keys())

        for key, value in params.items():
            setattr(self, key, value)
        self.data = data
    
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

    def save(self):
        """Saves the datum to disk"""

        obj = (self.params, self.data)
        self._saver(self._filename, obj)
