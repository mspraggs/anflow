from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from datetime import datetime
import hashlib
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from anflow.conf import settings
from anflow.core.wrappers import Datum
from anflow.db.models import CachedData
from anflow.utils.debug import debug_message
from anflow.utils.io import projectify
from anflow.utils.logging import logger



def hashgen(hash_object):
    """Generate an md5 hash using the pickle value of the specified object"""
    pickle_value = pickle.dumps(hash_object, 2)
    return hashlib.md5(pickle_value).hexdigest()

def file_cache_lookup(hash_object, base_path, timestamp=None):
    hash_value = hashgen(hash_object)
    file_path = os.path.join(base_path, hash_value + ".pkl")
    if os.path.exists(file_path):
        if timestamp:
            file_timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_timestamp > timestamp:
                return Datum.load(file_path).value
    return

def file_cache_dump(hash_object, base_path, datum):
    hash_value = hashgen(hash_object)
    file_path = os.path.join(base_path, hash_value + ".pkl")
    datum._filename = file_path
    datum.save()

def db_cache_lookup(hash_object, base_path, timestamp=None):
    hash_value = hashgen(hash_object)
    latest = (CachedData.data.filter(hash=hash_value, label=None)
              .order_by('-timestamp').first())
    if latest:
        if latest.timestamp < timestamp:
            return latest.value
    return

def db_cache_dump(hash_object, base_path, datum):
    hash_value = hashgen(hash_object)
    cached_data = CachedData(hash=hash_value, value=datum.value,
                             central_value=datum.central_value,
                             error=datum.error)
    cached_data.save()

def bin_data(data, binsize):
    return [sum(data[i:i+binsize]) / binsize
            for i in range(0, len(data) - binsize + 1, binsize)]

class Resampler(object):
    """Base resampling class - just returns the data as is"""

    name = 'base_resampler'

    def __init__(self, resample=True, average=False, binsize=1, cache='file',
                 cache_path=None):
        """Constructor - give the resampler a measurement function, tell it
        the format of the results paths, and whether to average the results
        at the end or just return the measurement on the resampled data"""

        self.do_resample = resample
        self.binsize = binsize
        self.average = average
        self.cache_path = projectify(cache_path or settings.CACHE_PATH)
        if cache == 'file':
            self.cache_lookup = file_cache_lookup
            self.cache_dump = file_cache_dump
            try:
                os.makedirs(self.cache_path)
            except OSError as e:
                debug_message(e)
        elif cache == 'db':
            self.cache_lookup = db_cache_lookup
            self.cache_dump = db_cache_dump
        else:
            self.cache_lookup = None
            self.cache_dump = None

    def __call__(self, data, function):
        """Pulls together all the resampling components - the main resampling
        entry point"""
        log = logger()
        # Create a unique filename for the cached resampled copies
        hash_object = (data.paramsdict(), self.average, self.binsize,
                       self.__class__.__name__)
        log.info("Checking for cached data")
        working_data = self.cache_lookup(hash_object, self.cache_path,
                                         data.timestamp)
        if not working_data:
            log.info("No cached data found")
            if self.do_resample:
                log.info("Resampling")
                working_data = self.resample(bin_data(data.value, self.binsize))
            else:
                log.info("No need to resample")
                working_data = bin_data(data.value, self.binsize)
            log.info("Saving new data to cache")
            self.cache_dump(hash_object, self.cache_path,
                            Datum(data.paramsdict(), working_data))

        log.info("Running model function across resampled data")
        results = map(function, working_data)
        log.info("Running model function on central value")
        centre = self._central_value(data, results, function)

        log.info("Computing error")
        error = self.error(results, centre)
        return results, centre, error

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
