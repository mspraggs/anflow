from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import md5
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

    def __init__(self, resample=True, compute_error=True, binsize=1):
        """Constructor - give the resampler a measurement function, tell it
        the format of the results paths, and whether to average the results
        at the end or just return the measurement on the resampled data"""

        self.do_resample = resample
        self.compute_error = compute_error
        self.binsize = binsize

    def __call__(self, data, function):
        """Pulls together all the resampling components - the main resampling
        entry point"""
        # Create a unique filename for the cached resampled copies
        hash_object = (data.paramsdict(), data.value)
        hash_value = md5.md5(pickle.dumps(hash_object, 2)).hexdigest()
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
            central_value = datum.central_value
        except (IOError, OSError) as e:
            debug_message(e)
            # If we've been asked to resample, then we compute the resampled
            # data and the central value using the resample function
            if self.do_resample:
                resampled_data = self.resample(bin_data(data.value,
                                                        self.binsize))
                working_data = resampled_data[0]
                central_value = resampled_data[1]
            else:
                # Otherwise use the supplied data, binning as necessary
                working_data = bin_data(data.value, self.binsize)
                central_value = data.central_value
            datum = Datum(data.paramsdict(), working_data, filename)
            datum.central_value = central_value
            datum.save()

        results = map(function, working_data)
        centre = function(central_value)

        if self.compute_error:
            error = self.error(results, centre)
            return results, centre, error
        else:
            return results, centre

    @staticmethod
    def resample(data):
        return data, sum(data) / len(data)

    @staticmethod
    def error(data, central_value):
        pass
