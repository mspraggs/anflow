from __future__ import absolute_import

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random

import pytest

from anflow.data import FileWrapper#, Datum, DataSet

@pytest.fixture
def random_wrapper(request, tmp_dir):

    data = random.sample(range(100), 10)
    filename = os.path.join(tmp_dir, 'data.pkl')
    with open(filename, 'w') as f:
        pickle.dump(data, f)

    timestamp = os.path.getmtime(filename)

    def loader(fname):
        with open(filename) as f:
            return pickle.load(f)

    request.addfinalizer(lambda: os.unlink(filename))

    return {'wrapper': FileWrapper(filename, loader),
            'data': data,
            'filename': filename,
            'loader': loader,
            'timestamp': timestamp}

class TestFilewrapper(object):

    def test_init(self, random_wrapper):
        """Test for __init__ function"""
        assert random_wrapper['wrapper'].filename == random_wrapper['filename']
        assert random_wrapper['wrapper'].loader == random_wrapper['loader']
        assert random_wrapper['wrapper'].timestamp == random_wrapper['timestamp']

    def test_data(self, random_wrapper):
        """Test function for property data"""
        assert random_wrapper['wrapper'].data == random_wrapper['data']
