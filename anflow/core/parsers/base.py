from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
import inspect
from itertools import product
import os
import re

from anflow.conf import settings
from anflow.core.data import DataSet, Datum



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

class BlindParser(BaseParser):
    """Parses all data according to arser for parsing raw data"""
    
    def __init__(self, parser, collect=None, study=None):
        """Create the parser and compile the regular expression"""
        super(BlindParser, self).__init__(study)

        self.parser = parser
        self.collect = collect

    def populate(self):
        """Loop through all files in the rawdata directory and parse the data"""

        result_paths = []
        for directory, dirs, files in os.walk(self.rawdata_dir):
            for f in files:
                result_paths.append(os.path.join(directory, f))
        result_paths.sort()

        temp_parsed_data = []
        for result_path in result_paths:
            datum = self.parser(result_path)
            if datum:
                temp_parsed_data.append(datum)

        if self.collect:
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
            for datum in temp_parsed_data:
                temp_params = copy.copy(datum.paramsdict())
                temp_params.pop(collect)
                if temp_params not in uncollected_params:
                    uncollected_params.append(temp_params)

            # Loops through the parameters we're not collecting according
            # to and build a list for each of these parameter sets
            for params in uncollected_params:
                def list_filter(datum):
                    datum_params = copy.copy(datum.paramsdict())
                    datum_params.pop(collect)
                    return datum_params == params
                filtered_list = filter(list_filter, temp_parsed_data)
                timestamps = map(lambda item: item._timestamp, filtered_list)
                collected_datum = Datum(params, map(lambda item: item.value,
                                                    filtered_list),
                                        timestamp=max(timestamps))
                self.parsed_data.append(collected_datum)
        else:
            self.parsed_data = DataSet(temp_parsed_data)

        self.set_path_format()

class GuidedParser(BaseParser):
    """Parses data based on a given path format and list of possible paremeter
    values"""

    def __init__(self, parser, path_template, collect=None, **kwargs):
        """Parse data into a dataset based on path template and parameter
        values"""
        super(GuidedParser, self).__init__()

        self.path_template = os.path.join(self.rawdata_dir, path_template)
        self.parser = parser
        self.collect = collect
        self.params = kwargs

    def populate(self):
        """Loop through all parameters and load the data using the parameters
        and the path template"""

        collect_params = {}
        for param in self.collect:
            collect_params[param] = self.params.pop(param)
            self.path_template = re.sub('{{ *{} *}}'.format(param),
                                        '{{{{{}}}}}'.format(param),
                                        self.path_template)
        
        for values in product(*self.params.values()):
            paramdict = dict(zip(self.params.keys(), values))
            sub_template = self.path_template.format(**paramdict)
            parsed_data = self.parser(sub_template, **collect_params)

            timestamps = []
            for collected_values in product(*collect_params.values()):
                collected_paramsdict = dict(zip(collect_params.keys(),
                                                collected_values))
                filename = sub_template.format(**collected_paramsdict)
                timestamps.append(os.path.getmtime(filename))
            self.parsed_data.append(Datum(paramdict, parsed_data,
                                          timestamp=max(timestamps)))

        self.set_path_format()
