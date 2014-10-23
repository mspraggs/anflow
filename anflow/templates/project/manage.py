from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys

from anflow.core import management

if __name__ == "__main__":
    os.environ.setdefault("ANFLOW_SETTINGS_MODULE",
                          "settings")
    management.execute_from_command_line(sys.argv)
