from __future__ import absolute_import

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random

import pytest

from anflow.data import FileWrapper, Datum, DataSet

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

@pytest.fixture
def random_datum(request, tmp_dir):

    data = random.sample(range(100), 10)
    params = {'a': 1, 'b': 2}

    datum = Datum(params, data, file_prefix=tmp_dir+'/some_measurement_')
    
    def fin():
        try:
            os.unlink(datum._filewrapper.filename)
        except OSError:
            pass
    
    request.addfinalizer(fin)

    return {'datum': datum,
            'data': data,
            'params': params}

class TestFilewrapper(object):

    def test_init(self, random_wrapper):
        """Test for __init__ function"""
        assert random_wrapper['wrapper'].filename == random_wrapper['filename']
        assert random_wrapper['wrapper'].loader == random_wrapper['loader']
        assert (random_wrapper['wrapper'].timestamp
                == random_wrapper['timestamp'])

    def test_data(self, random_wrapper):
        """Test function for property data"""
        assert not hasattr(random_wrapper['wrapper'], '_data')
        assert random_wrapper['wrapper'].data == random_wrapper['data']
        assert hasattr(random_wrapper['wrapper'], '_data')
        assert random_wrapper['wrapper']._data == random_wrapper['data']

class TestDatum(object):

    def test_init(self, random_datum, tmp_dir):
        """Test __init__ function"""
        expected_filename = tmp_dir + "/some_measurement_a1_b2.pkl"
        assert (random_datum['datum']._filewrapper.filename
                == expected_filename)
        assert random_datum['datum']._params == set(['a', 'b'])
        for attr, val in random_datum['params'].items():
            assert getattr(random_datum['datum'], attr) == val

    def test_params(self, random_datum):
        """Test that the parameters can be constructed properly"""
        assert random_datum['datum'].params == {'a': 1, 'b': 2}

    def test_save(self, random_datum, tmp_dir):
        """Test the save function of the Datum class"""
        random_datum['datum'].save()
        
        expected_filename = tmp_dir + "/some_measurement_a1_b2.pkl"
        assert os.path.exists(expected_filename)
        
        with open(expected_filename) as f:
            contents = pickle.load(f)
        assert contents[0] == random_datum['params']
        assert contents[1] == random_datum['data']
