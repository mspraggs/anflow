from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
import os
import sys

from anflow.conf import settings

def debug_message(*args):
    if settings.DEBUG:
        for msg in args:
            if isinstance(msg, Exception):
                last_frame = inspect.trace()[-1]
                fname = last_frame[1]
                lineno = last_frame[2]
                exc_type = sys.exc_info()[0]
                print("[DEBUG]: {}: {}: {}, line {}"
                      .format(exc_type.__name__, msg, fname, lineno))
            else:
                print("[DEBUG]: {}".format(msg))
