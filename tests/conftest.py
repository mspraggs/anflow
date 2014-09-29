from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from datetime import datetime
import logging
import os
import shutil

import pytest
from sqlalchemy import Column, Float, Integer, String

from anflow.core.wrappers import Datum
from anflow.db import Base, models



@pytest.fixture(scope="session")
def base_settings():
    from anflow.conf import settings, ENVIRONMENT_VARIABLE

    project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "test_project")

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

    return settings

@pytest.fixture(scope="session")
def settings(base_settings, request):
    try:
        os.makedirs(base_settings.PROJECT_ROOT)
    except OSError:
        pass

    def fin():
        shutil.rmtree(base_settings.PROJECT_ROOT, ignore_errors=True)
    request.addfinalizer(fin)
    return base_settings

@pytest.fixture(scope='session')
def MyModel(settings, request):

    class MyModel(models.Model):

        input_stream = [Datum({'foo': str(i), 'bar': 2 * i}, i**2)
                        for i in range(10)]
        foo = Column(String)
        bar = Column(Float)
        some_var = Column(Integer)

        @staticmethod
        def main(data, foo, bar, some_var):
            return data // some_var

    Base.metadata.create_all(settings.engine)
    request.addfinalizer(lambda: Base.metadata.drop_all(settings.engine))

    return MyModel
