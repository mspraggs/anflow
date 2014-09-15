from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
import os
import random
import string

import pytest

from anflow.db.data import Datum
from anflow.utils.io import projectify



class Obj(object):
    pass

@pytest.fixture
def random_datum(settings, request):
    randoms = ([random.randint(0, 100) for i in range(10)]
                + [10 * random.random() for i in range(10)])
    params = dict([("".join(random.sample(string.lowercase, 5)),
                    random.choice(randoms))
                    for i in range(10)])
    random.shuffle(randoms)
    filename = projectify("".join(random.sample(string.lowercase, 10)))
    datum = Datum(params, randoms, filename=filename)

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
    
class TestDatum(object):

    def test_constructor(self, random_datum):
        datum = random_datum.datum
        assert datum.value == random_datum.randoms
        assert datum._params == set(random_datum.params.keys())
        assert datum.timestamp == random_datum.timestamp
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
        assert loaded_datum.timestamp is not None
        datum.delete()
        assert not os.path.exists(random_datum.filename)
        assert loaded_datum.paramsdict() == random_datum.params
