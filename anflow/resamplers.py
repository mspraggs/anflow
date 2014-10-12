from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import collections
import json
import hashlib
import os

from anflow.data import Datum



def hashgen(hash_object):
    """Generate an md5 hash using the pickle value of the specified object"""
    pickle_value = json.dumps(hash_object)
    return hashlib.md5(pickle_value).hexdigest()

def cache_lookup(hash_object, base_path, timestamp):
    hash_value = hashgen(hash_object)
    file_path = os.path.join(base_path, hash_value + ".pkl")
    if os.path.exists(file_path):
        file_timestamp = os.path.getmtime(file_path)
        if file_timestamp > timestamp:
            return Datum.load(file_path).data
    return

def cache_dump(hash_object, base_path, datum):
    hash_value = hashgen(hash_object)
    file_path = os.path.join(base_path, hash_value + ".pkl")
    datum.filename = file_path
    datum.save()

def bin_data(data, binsize):
    return [sum(data[i:i+binsize]) / binsize
            for i in range(0, len(data) - binsize + 1, binsize)]

class Resampler(object):
    """Base resampling class"""

    def __init__(self, resample=True, average=False, binsize=1, cache_path=None,
                 error_name=None):
        """Constructor - creates the resampling object and the cache directory as
        required"""

        self.average = average
        self.binsize = binsize
        self._cache_path = cache_path
        self._cache = cache_path and resample
        self.do_resample = resample and self._cache
        self.error_name = error_name
        typename = self.__class__.__name__ + "Result"
        result_type = collections.namedtuple(typename,
                                             ['data', 'centre',
                                              'error', 'bins'])
        self.result_type = result_type
        self.bins = None

        if self._cache:
            try:
                os.makedirs(cache_path)
            except OSError:
                pass
        
    def __call__(self, function):
        """Pulls together all the resampling components - the main resampling
        entry point"""

        def decorator(data, *args, **kwargs):
            """Resampling function"""
            if self.do_resample:
                # Do the resampling as required
                hash_object = (data.filename, self.average, self.binsize,
                               self.__class__.__name__)
                # Check for cached data
                working_data = cache_lookup(hash_object, self._cache_path,
                                            data.timestamp)
                if not working_data:
                    # Resample data if it's not in the cache
                    working_data = self._resample(bin_data(data.data,
                                                           self.binsize))
                    if self._cache:
                        # Dump resampled data to cache if necessary
                        cache_dump(hash_object, self._cache_path,
                                   Datum(data.params, working_data))
            else:
                # If not resampling, then data is just the input data
                working_data = data.data.data

            if self.error_name:
                # If an error argument name is specified, add the error to
                # the kwargs
                try:
                    kwargs[self.error_name] = data.error
                except AttributeError:
                    # If there's no error in the input, compute it.
                    input_centre = sum(data.data) / len(data.data)
                    kwargs[self.error_name] = self._error(working_data,
                                                          input_centre)
            
            results = map(lambda datum: function(datum, *args, **kwargs),
                          working_data)
            centre = self._central_value(data, results,
                                         lambda datum: function(datum, *args,
                                                                **kwargs))
            error = self._error(results, centre)
            result_datum = self.result_type(data=results, centre=centre,
                                            error=error, bins=self.bins)
            return result_datum

        decorator.func = function

        return decorator

    def _resample(self, data):
        raise NotImplementedError

    def _central_value(self, datum, results, function):
        raise NotImplementedError
    
    @staticmethod
    def _error(data, central_value):
        raise NotImplementedError

class Bootstrap(Resampler):
    pass

class Jackknife(Resampler):
    pass
