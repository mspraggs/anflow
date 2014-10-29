from __future__ import absolute_import
from __future__ import unicode_literals

import os
import random
import shutil

import pytest

from anflow.data import Datum

from .utils import delete_shelve_files



@pytest.fixture(scope="session")
def tmp_dir(request):

    tmp_dir = os.path.join(os.path.dirname(__file__),
                           'tmp')
    try:
        os.makedirs(tmp_dir)
    except OSError:
        pass

    request.addfinalizer(lambda: shutil.rmtree(tmp_dir, ignore_errors=True))
    return tmp_dir

@pytest.fixture
def random_datum(request, tmp_dir):

    data = random.sample(range(100), 10)
    params = {'a': 1, 'b': 2}
    datum = Datum(params, data, file_prefix=tmp_dir+'/some_measurement_')
    
    request.addfinalizer(lambda: delete_shelve_files(datum.filename))

    return {'datum': datum,
            'data': data,
            'params': params}
