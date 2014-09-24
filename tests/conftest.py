from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import logging
import os
import shutil

import pytest

@pytest.fixture(scope="session")
def settings(request):
    from anflow.conf import settings, ENVIRONMENT_VARIABLE

    project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "test_project")
    try:
        os.makedirs(project_dir)
    except OSError:
        pass

    settings.DEBUG = True
    settings.PROJECT_ROOT = project_dir
    settings.CACHE_PATH = os.path.join(project_dir, "cache")
    
    settings.LOGGING_LEVEL = logging.INFO
    settings.LOGGING_CONSOLE = True
    settings.LOGGING_FORMAT = ("%(asctime)s : %(name)s : "
                               "%(levelname)s : %(message)s")
    settings.LOGGING_DATEFMT = "%d/%m/%Y %H:%M:%S"
    settings.LOGGING_FILE = (project_dir, "output_{}".format(datetime))

    settings.COMPONENT_TEMPLATE = "{study_name}/{component}"
    settings.RAWDATA_TEMPLATE = "rawdata"
    settings.RESULTS_TEMPLATE = "{study_name}/results"
    settings.REPORTS_TEMPLATE = "{study_name}/reports"

    settings.DB_PATH='sqlite:///{}/sqlite.db'.format(project_dir)

    settings.ACTIVE_STUDIES = ["foo",
                               "bar"]

    settings.configure()

    def fin():
        shutil.rmtree(project_dir, ignore_errors=True)
    request.addfinalizer(fin)
    return settings

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
