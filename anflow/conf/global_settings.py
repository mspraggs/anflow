from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

DEBUG = True

ANFLOW_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_TEMPLATE = os.path.join(ANFLOW_ROOT, "conf/project_template")
STUDY_TEMPLATE = os.path.join(ANFLOW_ROOT, "conf/study_template")

STUDY_COMPONENTS = ["views", "models"]
