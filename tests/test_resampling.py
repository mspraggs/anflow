from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import random

import numpy as np

from anflow.core.data import Datum
from anflow.lib.resamplers import bin_data, Bootstrap, Jackknife, Resampler

class TestFunctions(object):

    def test_bin_data(self):
        data = np.random.random(100)
        binned_data = bin_data(data, 10)
        # Check that the right number of bins have been computed
        assert len(binned_data) == 10
        # Check that each bin value is correct
        for i, datum in enumerate(binned_data):
            assert np.allclose(datum, data[10*i:10*(i+1)].mean())

class TestResampler(object):

    def test_constructor(self):
        # Test the default constructor first
        resampler = Resampler()
        attributes = ('do_resample', 'compute_error', 'binsize')
        for attr, val in zip(attributes, (True, True, 1)):
            assert getattr(resampler, attr) == val

        # Now test some random values
        do_resample, compute_error = random.sample((True, False), 2)
        binsize = random.randint(0, 100)
        resampler = Resampler(do_resample, compute_error, binsize)
        for attr, val in zip(attributes, (do_resample, compute_error, binsize)):
            assert getattr(resampler, attr) == val

    def test_call(self, settings):
        
        resampler = Resampler()
        # First we need to set up some data to do the resampling on
        data = [np.arange(10, dtype=np.float) + i for i in range(10)]
        params = {'foo': 12, 'bar': random.randint(0, 10)}
        datum = Datum(params, data, filename="data.pkl")
        datum.save()
        # The measurement function
        def func(x): return x**2

        results, centre, error = resampler(datum, func)
        
        assert np.allclose(np.arange(4.5, 14.0, 1.0) ** 2, centre)
        assert error is None
        assert len(results) == 10
        for d, r in zip(data, results):
            assert np.allclose(d**2, r)
        
    def test_resample(self):
        data = np.random.random(100)
        resampled_data, central_value = Resampler.resample(data)

        assert np.allclose(data, resampled_data)
        assert np.allclose(central_value, data.mean())

    def test_error(self):
        data = np.random.random(100)
        error = Resampler.error(data, data.mean())
        assert error is None

