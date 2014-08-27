from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect

import settings

class Parser(object):

    def __init__(self, pattern):
        """Create the parser and compile the regular expression"""

        self.populated = False
        self.regex = re.compile(path_template)

    def populate(self):
        """Collect the data and parameters from the raw data directory"""

        self.populated = True

    def parse(self, filename):
        """Parse the supplied filename"""
        if not self.populated:
            self.populate()
