from __future__ import absolute_import

import os

from anflow.data import Datum



def count_shelve_files(filename):
    """Counts files with shelve extensions with the specified base
    name"""
    counter = 0
    for extension in Datum._extensions:
        if os.path.exists(filename + extension):
            couter += 1
    return counter

def delete_shelve_files(filename):
    """Ensures that all shelve files are deleted"""

    for extension in Datum._extensions:
        try:
            os.unlink(filename + extension)
        except OSError:
            pass
