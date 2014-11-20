from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
from functools import wraps
import json
import hashlib
import logging
import os

from anflow.data import Datum



ResamplerResult = collections.namedtuple("ResamplerResult",
                                         ['data', 'centre',
                                          'error', 'bins'])

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
        self.do_resample = resample
        self.error_name = error_name
        self.bins = None
        self.log = logging.getLogger('anflow.resamplers.{}'
                                     .format(self.__class__.__name__))

        if self._cache:
            try:
                os.makedirs(cache_path)
            except OSError:
                pass
        
    def __call__(self, function):
        """Pulls together all the resampling components - the main resampling
        entry point"""

        @wraps(function)
        def decorator(data, *args, **kwargs):
            """Resampling function"""
            if self.do_resample:
                # Do the resampling as required
                hash_object = (data.filename, self.average, self.binsize,
                               self.__class__.__name__)
                # Check for cached data
                self.log.info("Checking cache for resampled data")
                working_data = cache_lookup(hash_object, self._cache_path,
                                            data.timestamp)
                if not working_data:
                    self.log.info("No cached data")
                    self.log.info("Resampling")
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
                    
                    input_centre = sum(working_data) / len(working_data)
                    kwargs[self.error_name] = self._error(working_data,
                                                          input_centre)
            results = []
            N = len(working_data)
            for i, datum in enumerate(working_data):
                self.log.info("Applying function to sample {} of {}".format(i + 1, N))
                result = function(datum, *args, **kwargs)
                if result is None:
                    self.log.warning("Measurement on sample returned None")
                    return
                results.append(result)
            if len(results) == 0:
                return
            if type(data.data) == ResamplerResult:
                centre_data = data.data
            else:
                centre_data = data
            self.log.info("Applying function to central value")
            centre = self._central_value(centre_data, results,
                                         lambda datum: function(datum, *args,
                                                                **kwargs))
            self.log.info("Computing error")
            error = self._error(results, centre)
            result_datum = ResamplerResult(data=results, centre=centre,
                                           error=error, bins=self.bins)
            return result_datum

        decorator.original = function
        decorator.resampled = None
        decorator.error_name = self.error_name

        return decorator

    def _resample(self, data):
        raise NotImplementedError

    def _central_value(self, datum, results, function):
        raise NotImplementedError
    
    @staticmethod
    def _error(data, central_value):
        raise NotImplementedError

class Jackknife(Resampler):

    def _central_value(self, data, results, function):
        if self.do_resample:
            if self.average:
                return function(sum(data.data) / len(data.data))
            else:
                return function(data.data)
        else:
            return function(data.centre)
    
    @staticmethod
    def _error(data, centre):
        N = len(data)
        deviations = map(lambda datum: (datum - centre)**2, data)
        return ((N - 1) / N * sum(deviations))**0.5

    def _resample(self, data):

        N = len(data)
        if self.average:
            data_sum = sum(data)
            resampled_data = [(data_sum - datum) / (N - 1) for datum in data]
        else:
            resampled_data = [data[:i] + data[i+1:] for i in range(N)]
        return resampled_data

class Bootstrap(Resampler):

    def __init__(self, resample=True, average=False, binsize=1, bins=None,
                 num_bootstraps=None, cache_path=None, error_name=None):
        """Initialize the bootstrap variables - bins and/or num_bootstraps"""

        super(Bootstrap, self).__init__(resample, average, binsize, cache_path,
                                        error_name)
        if not (bins or num_bootstraps):
            raise ValueError("You must specify either the bins to use or the "
                             "number of bootstraps")
        else:
            self.bins = bins
            self.num_bootstraps = num_bootstraps or len(bins)

    def _central_value(self, data, results, function):
        """Central value computation"""
        return function(sum(results) / len(results))

    @staticmethod
    def _error(data, centre):
        """Error computation"""
        N = len(data)
        deviations = map(lambda datum: (datum - centre)**2, data)
        return (1 / N * sum(deviations))**0.5

    def _resample(self, data):
        """Resample the supplied data"""

        N = len(data)
        if not self.bins:
            self.bins = [np.random.randint(N, size=N).tolist()
                         for i in range(self.num_bootstraps)]
        resampled_data = [[data[i] for i in sample_bins]
                          for sample_bins in self.bins]
        if self.average:
            return [sum(datum) / len(datum) for datum in resampled_data]
        else:
            return resampled_data
        
