from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
import os
import re

from anflow.conf import settings
from anflow.core.data import DataSet



class BaseParser(object):

    def __init__(self, study=None):

        component_regex = re.compile(re.sub(r'\{ *(?P<var>\w+) *\}',
                                            '(?P<\g<var>>.+)',
                                            settings.COMPONENT_TEMPLATE))
        if not study:
            stack = inspect.stack()
            for frame in stack:
                relative_path = os.path.relpath(frame[1], settings.PROJECT_ROOT)
                result = component_regex.search(relative_path)
                if study in settings.ACTIVE_STUDIES:
                    break
        self.study = study
        self.rawdata_dir = settings.RAWDATA_TEMPLATE.format(study_name=study)

        self.parsed_data = DataSet()
        self.populated = False

    def set_path_format(self):
        """Puts together a proposed results path for use by the model if
        necessary"""
        params = self.parsed_data[0].paramsdict()
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
