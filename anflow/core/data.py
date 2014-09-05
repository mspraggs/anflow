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

    def __init__(self, params, data, filename=None, timestamp=None):

        self._params = set(params.keys())
        self.value = data
        self._filename = filename
        
        for key, value in params.items():
            setattr(self, key, value)
            
        try:
            self._timestamp = timestamp or os.path.getmtime(filename)
        except OSError as e:
            debug_message(e)
            self._timestamp = None

    def paramsdict(self):
        return dict([(key, getattr(self, key)) for key in self._params])

    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
        
    def __setattr__(self, attr, value):
        non_params = ["value", "central_value", "error"]
        if not attr.startswith('_') and attr not in non_params:
            self._params.add(attr)
        return object.__setattr__(self, attr, value)

    def delete(self):
        os.unlink(self._filename)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._filename))
        except OSError as e:
            debug_message(e)

        save_object = [self.paramsdict(), self.value]
        try:
            save_object.append(self.central_value)
            save_object.append(self.error)
        except AttributeError as e:
            debug_message(e)
        save_object = tuple(save_object)
            
        with open(self._filename, 'wb') as f:
            pickle.dump(save_object, f, 2)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            file_contents = pickle.load(f)
        datum = cls(file_contents[0], file_contents[1], filename)
        try:
            datum.central_value = file_contents[2]
            datum.error = file_contents[3]
        except IndexError as e:
            debug_message(e)
        return datum

    def __repr__(self):
        output = object.__repr__(self) + "\n"
        output += "Datum Parameters\n"
        output += "================\n"
        output += "\n".join(["{}: {}".format(key, value)
                             for key, value in self.paramsdict().items()])
        return output

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
