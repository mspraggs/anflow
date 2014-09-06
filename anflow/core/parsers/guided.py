from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import copy
from itertools import product
import os
import re

from anflow.core.data import Datum
from anflow.core.parsers.base import BaseParser
from anflow.utils.logging import logger



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
        if self.populated:
            return
        log = logger()
        log.info("Populating GuidedParser")
        collect_params = {}
        params_copy = copy.copy(self.params)
        path_template_copy = self.path_template
        if self.collect:
            for param in self.collect:
                collect_params[param] = params_copy.pop(param)
                path_template_copy = re.sub('{{ *{} *}}'.format(param),
                                            '{{{{{}}}}}'.format(param),
                                            path_template_copy)
        
        for values in product(*params_copy.values()):
            paramdict = dict(zip(params_copy.keys(), values))
            sub_template = path_template_copy.format(**paramdict)
            parsed_data = self.parser(sub_template, **collect_params)

            timestamps = []
            for collected_values in product(*collect_params.values()):
                collected_paramsdict = dict(zip(collect_params.keys(),
                                                collected_values))
                filename = sub_template.format(**collected_paramsdict)
                timestamps.append(os.path.getmtime(filename))
            self.parsed_data.append(Datum(paramdict, parsed_data,
                                          timestamp=max(timestamps)))

        self.populated = True
        self.set_path_format()
