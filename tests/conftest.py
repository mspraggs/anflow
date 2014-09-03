from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import logging
import os
import shutil

import pytest

@pytest.fixture(scope="function")
def settings(request):
    from anflow.conf import settings, ENVIRONMENT_VARIABLE
    os.environ[ENVIRONMENT_VARIABLE] = 'anflow.conf.global_settings'
    settings.configure()

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
    settings.LOGGING_FORMAT = ("%(asctime)s : %(name)s : "
                               "%(levelname)s : %(message)s")
    settings.LOGGING_DATEFMT = "%d/%m/%Y %H:%M:%S"
    settings.LOGGING_FILE = (project_dir, "output_{}".format(datetime))

    settings.COMPONENT_TEMPLATE = os.path.join(project_dir,
                                               "{study_name}/{component}")
    settings.RAWDATA_TEMPLATE = os.path.join(project_dir, "rawdata")
    settings.RESULTS_TEMPLATE = os.path.join(project_dir,
                                             "{study_name}/results")
    settings.REPORTS_TEMPLATE = os.path.join(project_dir,
                                             "{study_name}/reports")

    def fin():
        shutil.rmtree(project_dir, ignore_errors=True)
    request.addfinalizer(fin)
    return settings