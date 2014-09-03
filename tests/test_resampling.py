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
            hash_object = (datum.paramsdict(), datum.value, average)
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
        # Since we're sampling randomly, we can only really check the bounds
        # the result must lie in.
        assert np.less_equal(centre, np.arange(9.0, 19.0, 1.0)**2).all()
        assert np.greater_equal(centre, np.arange(10)**2).all()

    def check_error(self, error):
        # Again, we can only really check bounds
        upper_bound = np.std([(np.arange(10) + i)**2 for i in range(10)],
                             axis=0)
        assert np.less_equal(error, upper_bound).all()
        assert np.greater_equal(error, np.zeros(error.shape)).all()

    def check_results(self, data, results, function):
        # Again, check bounds
        for result in results:
            assert np.less_equal(result, data[-1]**2).all()
            assert np.greater_equal(result, data[0]**2).all()

    def test_resample(self):
        data = np.random.random(100)
        resampler = self.resampler_class(average=False)
        resampled_data = resampler.resample(data)

        for datum in resampled_data:
            for subdatum in datum:
                assert subdatum in data

        resampler = self.resampler_class(average=True)
        resampled_data = resampler.resample(data)

        assert np.less_equal(resampled_data, data.max()).all()
        assert np.greater_equal(resampled_data, data.min()).all()

    def test_error(self):
        data = np.random.random(100)
        error = self.resampler_class.error(data, data.mean())
        assert np.allclose(error, np.std(data))

class TestJackknife(TestResampler):

    resampler_class = Jackknife

    def check_centre(self, centre):
        data = [np.arange(10, dtype=np.float) + i for i in range(10)]
        expected = np.mean(data, axis=0)**2
        assert np.allclose(centre, expected)

    def check_error(self, error):
        data = [np.arange(10, dtype=np.float) + i for i in range(10)]
        expected = np.array([8.62645884,
                             10.53956635,
                             12.45321078,
                             14.3671776,
                             16.2813531,
                             18.19567143,
                             20.1100918,
                             22.0245876,
                             23.93914073,
                             25.85373846])
        assert np.allclose(error, expected)

    def check_results(self, data, results, function):
        data = [np.arange(10, dtype=np.float) + i for i in range(10)]
        expected = [np.mean(data[:i] + data[i+1:], axis=0) ** 2
                    for i in range(10)]
        for r, e in zip(results, expected):
            assert np.allclose(r, e)

    def test_resample(self):

        data = np.random.random(100).tolist()
        resampler = self.resampler_class(average=False)
        resampled_data = resampler.resample(data)

        for datum in resampled_data:
            for subdatum in datum:
                assert subdatum in data

        resampler = self.resampler_class(average=True)
        resampled_data = resampler.resample(data)
        expected_data = np.array([(sum(data) - data[i]) / (len(data) - 1)
                                  for i in range(100)])
        
        assert np.allclose(resampled_data, expected_data)

    def test_error(self):
        data = np.random.random(100)
        error = self.resampler_class.error(data, data.mean())
        assert np.allclose(error, np.sqrt(99) * np.std(data))
