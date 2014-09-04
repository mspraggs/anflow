from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from itertools import product
import os
import re

from anflow.core.data import Datum
from anflow.core.parsers import BaseParser



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
