from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
import os

from anflow.core.data import DataSet, Datum
from anflow.core.parsers.base import BaseParser



class BlindParser(BaseParser):
    """Parses all data according to parser for parsing raw data"""
    
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

        self.populated = True
        self.set_path_format()
