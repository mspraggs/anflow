from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
import os
import random
import string

import pytest

from anflow.core.data import Datum, DataSet
from anflow.utils.io import projectify



class Obj(object):
    pass

@pytest.fixture()
def random_datum(settings, request):
    randoms = ([random.randint(0, 100) for i in range(10)]
                + [10 * random.random() for i in range(10)])
    params = dict([("".join(random.sample(string.lowercase, 5)),
                    random.choice(randoms))
                    for i in range(10)])
    random.shuffle(randoms)
    filename = projectify("".join(random.sample(string.lowercase, 10)))
    datum = Datum(params, randoms, filename)

    def fin():
        try:
            os.unlink(datum._filename)
        except OSError:
            pass
    request.addfinalizer(fin)

    ret = Obj()
    ret.datum = datum
    ret.randoms = randoms
    ret.params = params
    ret.filename = filename
    ret.timestamp = None
    
    return ret

@pytest.fixture()
def random_dataset(random_datum, settings, request):
    dataset = DataSet()
    for i in range(10):
        datum = copy.copy(random_datum.datum)
        datum.some_value = i
        datum._filename = projectify("datum{}.pkl".format(i))
        dataset.append(datum)
    return dataset
    
class TestDatum(object):

    def test_constructor(self, random_datum):
        datum = random_datum.datum
        assert datum.value == random_datum.randoms
        assert datum._params == set(random_datum.params.keys())
        assert datum._timestamp == random_datum.timestamp
        assert datum._filename == random_datum.filename
        
        for key, value in random_datum.params.items():
            assert getattr(datum, key) == value

    def test_paramsdict(self, random_datum):

        assert random_datum.datum.paramsdict() == random_datum.params

    def test_save_delete_load(self, random_datum):

        datum = random_datum.datum
        datum.save()
        loaded_datum = Datum.load(random_datum.filename)
        assert os.path.exists(random_datum.filename)
        datum.delete()
        assert not os.path.exists(random_datum.filename)
        assert loaded_datum.paramsdict() == random_datum.params

class TestDataSet(object):

    def test_constructor(self, random_datum):
        datum = random_datum.datum
        dataset = DataSet([datum])

    def test_filter(self, random_dataset):
        for i in range(10):
            assert len(random_dataset.filter(some_value=i))

    def test_save_delete(self, settings, random_dataset):
        random_dataset.save()
        for i in range(10):
            assert os.path.exists(os.path.join(settings.PROJECT_ROOT,
                                               'datum{}.pkl'.format(i)))
        random_dataset.delete()
        for i in range(10):
            assert not os.path.exists(os.path.join(settings.PROJECT_ROOT,
                                                   'datum{}.pkl'.format(i)))
