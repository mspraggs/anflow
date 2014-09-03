from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from anflow.conf import settings
from anflow.core.data import Datum
from anflow.utils.debug import debug_message



def bin_data(data, binsize):
    return [sum(data[i:i+binsize]) / binsize
            for i in range(0, len(data) - binsize + 1, binsize)]

class Resampler(object):
    """Base resampling class - just returns the data as is"""

    name = 'base_resampler'

    def __init__(self, resample=True, compute_error=True, average=False,
                 binsize=1):
        """Constructor - give the resampler a measurement function, tell it
        the format of the results paths, and whether to average the results
        at the end or just return the measurement on the resampled data"""

        self.do_resample = resample
        self.compute_error = compute_error
        self.binsize = binsize
        self.average = average # Determines whether to compute the mean of
        # the resampled dataset (could save some computing time)

    def __call__(self, data, function):
        """Pulls together all the resampling components - the main resampling
        entry point"""
        # Create a unique filename for the cached resampled copies
        hash_object = (data.paramsdict(), data.value)
        hash_value = hashlib.md5(pickle.dumps(hash_object, 2)).hexdigest()
        filename = os.path.join(settings.CACHE_PATH,
                                "{}.{}.binsize{}.pkl"
                                .format(hash_value, self.__class__.__name__,
                                        self.binsize))
        # Make the directory for the cached data
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as e:
            debug_message(e)
        # Check whether the cached data is older than the raw data. If so, we
        # need to resample and update the cache
        try:
            if data._timestamp > os.path.getmtime(filename):
                raise OSError('Cached jackknives out of date')
            datum = Datum.load(filename)
            working_data = datum.value
        except (IOError, OSError) as e:
            debug_message(e)
            # If we've been asked to resample, then we compute the resampled
            # data and the central value using the resample function
            if self.do_resample:
                working_data = self.resample(bin_data(data.value, self.binsize))
            else:
                # Otherwise use the supplied data, binning as necessary
                working_data = bin_data(data.value, self.binsize)
            datum = Datum(data.paramsdict(), working_data, filename)
            datum.save()

        try:
            filename = os.path.join(settings.CACHE_PATH,
                                "{}.{}.binsize{}.binnums.pkl"
                                .format(hash_value, self.__class__.__name__,
                                        self.binsize))
            with open(filename, 'wb') as f:
                pickle.dump(self.binset, f, 2)
        except AttributeError:
            pass

        results = map(function, working_data)
        centre = self._central_value(data, results, function)

        if self.compute_error:
            error = self.error(results, centre)
            return results, centre, error
        else:
            return results, centre

    def resample(self, data):
        return data

    def _central_value(self, datum, results, function):
        if self.do_resample:
            if self.average:
                return function(sum(datum.value) / len(datum.value))
            else:
                return function(datum.value)
        else:
            return function(datum.central_value)
    
    @staticmethod
    def error(data, central_value):
        pass
