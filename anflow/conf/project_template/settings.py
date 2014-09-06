from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import logging
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = 'cache'

LOGGING_LEVEL = logging.INFO
LOGGING_CONSOLE = True
LOGGING_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
LOGGING_DATEFMT = "%d/%m/%Y %H:%M:%S"
LOGGING_FILE = "output_{}".format(time.strftime("%d-%m-%Y_%H:%M:%S"))

COMPONENT_TEMPLATE = "{study_name}/{component}"
RAWDATA_TEMPLATE = "rawdata"
RESULTS_TEMPLATE = "{study_name}/results"
REPORTS_TEMPLATE = "{study_name}/reports"

ACTIVE_STUDIES = [
    ]
