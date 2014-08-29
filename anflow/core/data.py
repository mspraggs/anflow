from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function



class Datum(object):

    def __init__(self, params, data):

        for key, value in params.items():
            setattr(self, key, value)

        self.value = data
        self._params = params

    def paramsdict(self):
        return self._params

    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
        
    def __setattr__(self, attr, value):
        return object.__setattr__(self, attr, value)

class DataSet(list):

    def __init__(self, *args):
        list.__init__(self, *args)

    def filter(self, **kwargs):
        """Filter the data"""

        out = self
        for key, value in kwargs.items():
            def filter_function(datum):
                return datum[0][key] == value
            out = filter(filter_function, out)
        return out

    def __getitem__(self, index):
        params, datum = list.__getitem__(self, index)
        return Datum(params, datum)

    def __setitem__(self, index, datum):
        params = value.paramsdict()
        list.__setitem__(self, index, (params, datum.value))

    def __getslice__(self, i, j):
        return DataSet(list.__getslice__(self, i, j))
    
    def __repr__(self):
        return object.__repr__(self)
