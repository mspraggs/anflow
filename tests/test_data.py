from __future__ import absolute_import

from itertools import product
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random
import shelve

import pytest

from anflow.data import (generate_filename, gather_data,
                         FileWrapper, Datum, DataSet)



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
            os.unlink(datum._filename)
        except OSError:
            pass
    
    request.addfinalizer(fin)

    return {'datum': datum,
            'data': data,
            'params': params}

@pytest.fixture
def random_dataset(request, tmp_dir):

    data = random.sample(range(100), 10)
    dataset = DataSet()
    filenames = []
    all_params = []
    for a, b in product(range(1, 5), range(7, 10)):
        params = {'a': a, 'b': b}
        all_params.append(params)
        datum = Datum(params, data, file_prefix=tmp_dir+'/')
        filenames.append(datum._filename)        
        dataset.append(datum)

    def fin():
        for filename in filenames:
            try:
                os.unlink(filename)
            except OSError:
                pass

    request.addfinalizer(fin)

    return {'dataset': dataset, 'params': all_params}

class TestFunctions(object):

    def test_generate_filename(self):
        """Test generate_filename"""
        params = {'a': 4, 'blah': 2, 'ds': 'ok'}
        filename = generate_filename(params, "some_prefix_", ".pkl")
        assert filename == "some_prefix_a4_blah2_dsok.pkl"

    def test_gather_data(self, random_dataset, tmp_dir):
        """Test gather_data"""
        random_dataset['dataset'].save()

        data_params = [{'a': i} for i in range(1, 5)]
        params = [{'b': i} for i in range(7, 10)]
        data = gather_data(tmp_dir, data_params, params=params)
        assert len(data) == 12
        data = gather_data(tmp_dir, data_params=random_dataset['params'])
        assert len(data) == 12

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
        assert random_datum['datum']._filename == expected_filename
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

        shelf = shelve.open(expected_filename, protocol=2)
        assert shelf['params'] == random_datum['params']
        assert shelf['data'] == random_datum['data']
        shelf.close()

    def test_load(self, random_datum, tmp_dir):
        """Test the load function of the Datum class"""
        filename = os.path.join(tmp_dir, 'some_file.pkl')
        shelf = shelve.open(filename, protocol=2)
        shelf['params'] = random_datum['params']
        shelf['data'] = random_datum['data']
        shelf.close()

        new_datum = Datum.load(filename)
        assert not hasattr(new_datum, '_data')
        assert new_datum.params == random_datum['params']
        assert new_datum.data == random_datum['data']

class TestDataSet(object):

    def test_filter(self, random_dataset):
        """Test filter feature of dataset"""
        assert len(random_dataset['dataset']) == 12
        assert len(random_dataset['dataset'].filter(a=2)) == 3
        assert len(random_dataset['dataset'].filter(a__gt=2)) == 6
        assert len(random_dataset['dataset'].filter(a__lt=2)) == 3
        assert len(random_dataset['dataset'].filter(a__gte=2)) == 9
        assert len(random_dataset['dataset'].filter(a__lte=2)) == 6

        assert len(random_dataset['dataset'].filter(a=2, b__gt=8)) == 1

    def test_save(self, random_dataset, tmp_dir):

        random_dataset['dataset'].save()
        for params in random_dataset['params']:
            filename = "a{a}_b{b}.pkl".format(**params)
            expected_path = os.path.join(tmp_dir, filename)
            assert os.path.exists(expected_path)
