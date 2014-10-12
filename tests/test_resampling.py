from __future__ import absolute_import
from __future__ import unicode_literals

import os
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random
import shelve
import shutil
import time

import numpy as np
import pytest

from anflow.data import Datum
from anflow.resamplers import (bin_data, cache_lookup, cache_dump, hashgen,
                               Bootstrap, Jackknife, Resampler)

from .utils import delete_shelve_files



@pytest.fixture
def resampler(tmp_dir, request):
    cache_path = cache_path=os.path.join(tmp_dir, "cache")

    class MyResampler(Resampler):

        @staticmethod
        def _error(data, centre):
            return centre

        def _central_value(self, datum, results, func):
            return func(sum(datum.data) / len(datum.data))

        def _resample(self, data):
            return data
    
    resampler = MyResampler(resample=True, average=True, binsize=1,
                            cache_path=cache_path, error_name='error')
    request.addfinalizer(lambda: shutil.rmtree(cache_path, ignore_errors=True))
    
    return {"resampler": resampler, "cache_path": cache_path, "do_resample": True,
            "binsize": 1, "average": True, 'error_name': 'error'}

@pytest.fixture
def cached_datum(tmp_dir, request):
    obj = ("foo", "bar", 1)
    filename = os.path.join(tmp_dir, '36720cc7aec4fa2fe7625f72ea4cfdd4.pkl')
    
    data = random.sample(range(100), 10)
    params = {'a': 1, 'b': 2}
    timestamp = time.time()
    shelf = shelve.open(filename, protocol=2)
    shelf[b'params'] = params
    shelf[b'data'] = data
    shelf[b'timestamp'] = timestamp
    shelf.close()

    request.addfinalizer(lambda: delete_shelve_files(filename))

    return {'filename': filename, 'obj': obj, 'data': data}

class TestFunctions(object):

    def test_bin_data(self):
        """Test bin_data"""
        data = np.random.random(100)
        binned_data = bin_data(data, 10)
        # Check that the right number of bins have been computed
        assert len(binned_data) == 10
        # Check that each bin value is correct
        for i, datum in enumerate(binned_data):
            assert np.allclose(datum, data[10*i:10*(i+1)].mean())

    def test_hashgen(self):
        "Test hashgen"
        obj = ('foo', 'bar', 1)
        thehash = hashgen(obj)
        assert thehash == '36720cc7aec4fa2fe7625f72ea4cfdd4'

    def test_cache_lookup(self, cached_datum, tmp_dir):
        """Test cache_lookup"""
        result = cache_lookup(cached_datum['obj'], tmp_dir, 0)
        assert result == cached_datum['data']
        result = cache_lookup(cached_datum['obj'], tmp_dir, time.time())
        assert not result

    def test_cache_dump(self, tmp_dir, random_datum):
        """Test cache_dump"""
        obj = ('foo', 'bar', 1)
        cache_dump(obj, tmp_dir, random_datum['datum'])
        filename = os.path.join(tmp_dir, '36720cc7aec4fa2fe7625f72ea4cfdd4.pkl')
        assert os.path.exists(filename)

        shelf = shelve.open(filename, protocol=2)
        assert shelf[b'params'] == random_datum['params']
        assert shelf[b'data'] == random_datum['data']
        shelf.close()

class TestResampler(object):

    def test_init(self, resampler):
        """Test basic resampler constructor"""
        assert resampler['resampler']._cache_path == resampler['cache_path']
        for attr in ["do_resample", "binsize", "average", "error_name"]:
            assert getattr(resampler['resampler'], attr) == resampler[attr]
        assert os.path.exists(resampler['cache_path'])
        assert resampler['resampler']._cache
        assert resampler['resampler'].result_type.__name__ == "ResamplerResult"
