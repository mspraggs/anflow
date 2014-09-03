from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle
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

    resampler_class = Resampler

    def check_centre(self, centre):
        assert np.allclose(np.arange(4.5, 14.0, 1.0) ** 2, centre)

    def check_error(self, error):
        assert error is None

    def check_results(self, data, results, function):
        assert len(results) == 10
        for d, r in zip(data, results):
            assert np.allclose(function(d), r)

    def test_constructor(self):
        # Test the default constructor first
        resampler = self.resampler_class()
        attributes = ('do_resample', 'compute_error', 'average', 'binsize')
        for attr, val in zip(attributes, (True, True, False, 1)):
            assert getattr(resampler, attr) == val

        # Now test some random values
        truefalse = [True, False] * 100
        do_resample, compute_error, average = random.sample(truefalse, 3)
        binsize = random.randint(0, 100)
        args = (do_resample, compute_error, average, binsize)
        resampler = self.resampler_class(*args)
        for attr, val in zip(attributes, args):
            assert getattr(resampler, attr) == val

    def test_call(self, settings):

        functions = [lambda x: x**2, lambda x: (sum(x)/ len(x))**2]

        for average, function in zip((True, False), functions):
        
            resampler = self.resampler_class(average=average)
            # First we need to set up some data to do the resampling on
            data = [np.arange(10, dtype=np.float) + i for i in range(10)]
            params = {'foo': 12, 'bar': random.randint(0, 10)}
            datum = Datum(params, data,
                          filename=os.path.join(settings.PROJECT_ROOT,
                                                "data.pkl"))
            datum.save()
            # The measurement function

            # Compute the name of the cached resampled file
            hash_object = (datum.paramsdict(), datum.value)
            data_hash = hashlib.md5(pickle.dumps(hash_object, 2)).hexdigest()
            filename = "{}.{}.binsize1.pkl".format(data_hash,
                                                   resampler.__class__.__name__)

            for i in range(2):
                results, centre, error = resampler(datum, function)
                self.check_centre(centre)
                self.check_error(error)
                self.check_results(data, results, function)
                assert os.path.exists(os.path.join(settings.CACHE_PATH,
                                                   filename))

    def test_resample(self):
        data = np.random.random(100)
        resampler = self.resampler_class()
        resampled_data = resampler.resample(data)

        assert np.allclose(data, resampled_data)

    def test_error(self):
        data = np.random.random(100)
        error = self.resampler_class.error(data, data.mean())
        assert error is None

class TestBootstrap(TestResampler):

    resampler_class = Bootstrap

    def check_centre(self, centre):

        pass#assert np.less(centre, )centre is None

    def check_error(self, error):
        pass

    def check_results(self, data, results, function):
        pass

    def test_resample(self):
        pass

    def test_error(self):
        pass

class TestJackknife(TestResampler):

    resampler_class = Jackknife

    def check_centre(self, centre):
        pass

    def check_error(self, error):
        pass

    def check_results(self, data, results, function):
        pass

    def test_resample(self):
        pass

    def test_error(self):
        pass

