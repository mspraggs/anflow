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



class Datum(object):
    def __init__(self, params, data, central_value=None, error=None,
                 filename=None, timestamp=None):
        self._params = set(params.keys())
        self.value = data
        self._filename = filename
        self.central_value = central_value
        self.error = error
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
        save_object = (self.paramsdict(), self.value, self.central_value,
                       self.error)        
        with open(self._filename, 'wb') as f:
            pickle.dump(save_object, f, 2)
            
    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            params, value, central_value, error = pickle.load(f)
        datum = cls(params, value, central_value, error, filename)
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
