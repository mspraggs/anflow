from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(PROJECT_ROOT, "rawdata")
LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"
LOGGING_DATEFMT = "%d/%m/%Y %H:%M:%S"
LOGGING_FILE = "output_{}".format(datetime)

COMPONENT_PATH = "{study_name}/{component}"

INSTALLED_STUDIES = [
    ]
