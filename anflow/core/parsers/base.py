from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
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

        temp_parsed_data = []
        for result_path in result_paths:
            temp_parsed_data.append(self.parser(result_path))

        if collect:
            # This block is executed if the user wants to group the data
            # according the parameter specified in collect. This means that
            # each element in self.parsed_data will contain a list of data,
            # each corresponding to a unique value of the specified parameter.
            # Basically it's a way of collecting all data for a specified
            # parameter so we can do some resampling in some way.
            # This code is messy and potentially slow, so if it can be cleaned
            # up then so much the better
            
            uncollected_params = []
            # Get the unique parameters after the collect parameter is removed
            for params, datum in temp_parsed_data:
                temp_params = copy.copy(params)
                temp_params.pop(collect)
                if temp_params not in uncollected_params:
                    uncollected_params.append(temp_params)

            for params in uncollected_params:
                def list_filter(datum):
                    datum_params = copy.copy(datum[0])
                    #print(datum_params.keys())
                    datum_params.pop(collect)
                    return datum_params == params
                filtered_list = filter(list_filter, temp_parsed_data)
                self.parsed_data.append((params, map(lambda item: item[1],
                                                     filtered_list)))
        else:
            self.parsed_data = temp_parsed_data

        print(self.parsed_data[0][0])
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
