from __future__ import absolute_import

from itertools import product
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import random
import shelve
import time

import pytest

from anflow.data import generate_filename, FileWrapper, Datum, DataSet

from .utils import count_shelve_files, delete_shelve_files



@pytest.fixture
def random_wrapper(request, tmp_dir):

    data = random.sample(range(100), 10)
    filename = os.path.join(tmp_dir, 'data.pkl')
    with open(filename, 'w') as f:
        pickle.dump(data, f)

    timestamp = os.path.getmtime(filename)

    def loader(fname):
        with open(fname) as f:
            return pickle.load(f)

    request.addfinalizer(lambda: os.unlink(filename))

    return {'wrapper': FileWrapper(filename, loader),
            'data': data,
            'filename': filename,
            'loader': loader,
            'timestamp': timestamp}

@pytest.fixture
def random_datum_file(tmp_dir, random_datum, request):

    data = random.sample(range(100), 10)
    params = {'a': 1, 'b': 2}

    timestamp = time.time()
    filename = tmp_dir + "/a1_b1.pkl"
    shelf = shelve.open(filename, protocol=2)
    shelf['params'] = random_datum['params']
    shelf['data'] = random_datum['data']
    shelf['timestamp'] = timestamp
    shelf.close()

    request.addfinalizer(lambda: delete_shelve_files(filename))

    return {'filename': filename, 'params': params, 'timestamp': timestamp,
            'data': data}

@pytest.fixture(scope='class')
def random_dataset(request, tmp_dir):

    data = random.sample(range(100), 10)
    filenames = []
    all_params = []
    for a, b in product(range(1, 5), range(7, 10)):
        params = {'a': a, 'b': b}
        all_params.append(params)
        filename = "_".join(["{}{}".format(key, value)
                             for key, value in params.items()])
        filename = "{}/{}.pkl".format(tmp_dir, filename)
        shelf = shelve.open(filename, 'c')
        shelf['params'] = params
        shelf['data'] = data
        shelf['timestamp'] = time.time()
        shelf.close()
        filenames.append(filename)
        
    dataset = DataSet(all_params, tmp_dir + '/')

    def fin():
        for filename in filenames:
            delete_shelve_files(filename)
    request.addfinalizer(fin)

    return {'dataset': dataset, 'params': all_params}

class TestFunctions(object):

    def test_generate_filename(self):
        """Test generate_filename"""
        params = {'a': 4, 'blah': 2, 'ds': 'ok'}
        filename = generate_filename(params, "some_prefix_", ".pkl")
        assert filename == "some_prefix_a4_blah2_dsok.pkl"

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
        t1 = time.time()
        random_datum['datum'].save()
        t2 = time.time()
        
        expected_filename = tmp_dir + "/some_measurement_a1_b2.pkl"
        assert os.path.exists(expected_filename)

        shelf = shelve.open(expected_filename, protocol=2)
        assert shelf['params'] == random_datum['params']
        assert shelf['data'] == random_datum['data']
        assert t1 < shelf['timestamp'] < t2
        shelf.close()

    def test_load(self, random_datum_file, tmp_dir):
        """Test the load function of the Datum class"""
        new_datum = Datum.load(random_datum_file["filename"])
        assert not hasattr(new_datum, '_data')
        assert new_datum.params == random_datum_file['params']
        assert new_datum.timestamp == random_datum_file["timestamp"]

    def test_delete(self, random_datum_file, tmp_dir):
        """Test Datum.delete"""        
        new_datum = Datum.load(random_datum_file["filename"])
        assert count_shelve_files(random_datum_file["filename"]) > 0
        new_datum.delete()
        assert count_shelve_files(random_datum_file["filename"]) == 0

class TestDataSet(object):

    def test_init(self, random_dataset, tmp_dir):

        assert random_dataset['dataset']._params == random_dataset['params']
        assert random_dataset['dataset']._prefix == tmp_dir + '/'

    def test_filter(self, random_dataset):
        """Test filter feature of dataset"""
        assert len(random_dataset['dataset']._params) == 12
        assert len(random_dataset['dataset'].filter(a=2)._params) == 3
        assert len(random_dataset['dataset'].filter(a__gt=2)._params) == 6
        assert len(random_dataset['dataset'].filter(a__lt=2)._params) == 3
        assert len(random_dataset['dataset'].filter(a__gte=2)._params) == 9
        assert len(random_dataset['dataset'].filter(a__lte=2)._params) == 6

        assert len(random_dataset['dataset'].filter(a=2, b__gt=8)._params) == 1

    def test_all(self, random_dataset):
        """Test for DataSet.all"""
        assert isinstance(random_dataset['dataset'].all(), list)
        assert len(random_dataset['dataset'].all()) == 12
        for datum in random_dataset['dataset'].all():
            assert isinstance(datum, Datum)

    def test_first(self, random_dataset):
        """Test for DataSet.first"""
        assert isinstance(random_dataset['dataset'].first(), Datum)

    def test_iter(self, random_dataset):
        """Test for DataSet.__iter__"""

        counter = 0
        for datum in random_dataset['dataset']:
            assert isinstance(datum, Datum)
            counter += 1

        assert counter == len(random_dataset['params'])
