from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect

import re

import settings

class Parser(object):

    def __init__(self, pattern):
        """Create the parser and compile the regular expression"""

        self.populated = False
        self.regex = re.compile(pattern)
        self.parsed_data = []

    def populate(self):
        """Collect the data and parameters from the raw data directory"""

        print(inspect.stack())
        self.populated = True

    def parse(self, filename):
        """Parse the supplied filename"""
        if not self.populated:
            self.populate()

    def __iter__(self):
        self.current = 0
        return self

    def next(self):
        try:
            self.current += 1
            return self.parsed_data[self.current]        
        except IndexError:
            raise StopIteration
