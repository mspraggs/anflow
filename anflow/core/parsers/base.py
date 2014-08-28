from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
import os
import re

import settings

class Parser(object):
    """Base parser for parsing raw data"""
    
    def __init__(self, parser, collect=None, study=None):
        """Create the parser and compile the regular expression"""

        self.populated = False
        self.parsed_data = []
        self.parser = parser

        if not study:
            stack = inspect.stack()
            for frame in stack:
                relative_path = os.path.relpath(frame[1], settings.PROJECT_ROOT)
                study = os.path.split(relative_path)[0]
                if study in settings.ACTIVE_STUDIES:
                    break
        self.study = study

        rawdata_dir = settings.RAWDATA_TEMPLATE.format(study_name=study)

        result_paths = []
        for directory, dirs, files in os.walk(rawdata_dir):
            for f in files:
                result_paths.append(os.path.join(directory, f))
        result_paths.sort()
        for result_path in result_paths:
            self.parsed_data.append(self.parser(result_path))

        params = self.parsed_data[0][0].keys()
        self.path_format = "_".join(["{}{{{}}}".format(param, param)
                                     for param in params])
        self.path_format += ".pkl"

    def __iter__(self):
        self.current = 0
        return self

    def next(self):
        try:
            self.current += 1
            return self.parsed_data[self.current - 1]        
        except IndexError:
            raise StopIteration
