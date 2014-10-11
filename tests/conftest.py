from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime
import logging
import os
import random
import shutil
import sys

import pytest
from sqlalchemy import Column, Float, Integer, String

from anflow.data import Datum
from anflow.db import Base, models

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
    
    request.addfinalizer(lambda: delete_shelve_files(datum._filename))

    return {'datum': datum,
            'data': data,
            'params': params}

@pytest.fixture(scope="session")
def base_settings():
    from anflow.conf import settings, ENVIRONMENT_VARIABLE

    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')

    project_dir = os.path.join(tmp_dir, 'test_project')

    settings.tmp_dir = tmp_dir
    settings.DEBUG = True
    settings.PROJECT_ROOT = project_dir
    settings.CACHE_PATH = os.path.join(project_dir, "cache")
    
    settings.LOGGING_LEVEL = logging.INFO
    settings.LOGGING_CONSOLE = True
    settings.LOGGING_FORMAT = ("%(asctime)s : %(name)s : "
                               "%(levelname)s : %(message)s")
    settings.LOGGING_DATEFMT = "%d/%m/%Y %H:%M:%S"
    settings.LOGGING_FILE = os.path.join(project_dir,
                                         "output_{}".format(datetime.now()))

    settings.COMPONENT_TEMPLATE = "{study_name}/{component}"
    settings.RAWDATA_TEMPLATE = "rawdata"
    settings.RESULTS_TEMPLATE = "{study_name}/results"
    settings.REPORTS_TEMPLATE = "{study_name}/reports"

    settings.DB_PATH='sqlite:///{}/sqlite.db'.format(project_dir)

    settings.ACTIVE_STUDIES = ["foo",
                               "bar"]

    settings.configure()

    sys.path.insert(0, settings.PROJECT_ROOT)

    return settings

@pytest.fixture(scope="session")
def settings(base_settings, request):
    try:
        os.makedirs(base_settings.PROJECT_ROOT)
    except OSError:
        pass

    def fin():
        shutil.rmtree(base_settings.tmp_dir, ignore_errors=True)
    request.addfinalizer(fin)
    return base_settings

@pytest.fixture(scope='session')
def MyModelBase(settings):
    
    class MyModel(models.Model):

        input_stream = [Datum({'foo': str(i), 'bar': 2 * i}, i**2)
                        for i in range(10)]
        foo = Column(String)
        bar = Column(Float)
        some_var = Column(Integer)

        @staticmethod
        def main(data, foo, bar, some_var):
            return data // some_var

    return MyModel

@pytest.fixture(scope='session')
def MyModel(MyModelBase, settings, request):

    Base.metadata.create_all(settings.engine)
    request.addfinalizer(lambda: Base.metadata.drop_all(settings.engine))

    return MyModelBase
