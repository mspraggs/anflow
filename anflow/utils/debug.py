from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys

from anflow.conf import settings

def debug_message(*args):
    if settings.DEBUG:
        for msg in args:
            if isinstance(msg, Exception):
                exc_type = sys.exc_info()[0]
                exc_obj = sys.exc_info()[1]
                exc_tb = sys.exc_info()[2]
                fname = os.path.relpath(exc_tb.tb_frame.f_code.co_filename,
                                        settings.ANFLOW_ROOT)
                print("[DEBUG]: {}: {}: {} {}"
                      .format(exc_type.__name__, msg, fname,
                              exc_tb.tb_lineno))
            else:
                print("[DEBUG]: {}".format(msg))
