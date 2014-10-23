from __future__ import absolute_import
from __future__ import unicode_literals

import inspect
from itertools import chain, product
import os
import re

from anflow.data import FileWrapper



class Parser(object):

    def __init__(self):
        """Parser constructor"""

        self.parsed_data = []
        self.populated = False

    def populate(self):
        """Empty populate function"""
        raise NotImplementedError

    def __iter__(self):
        """Parser iterator"""
        if not self.populated:
            self.populate()
        return self.parsed_data.__iter__()

    def __len__(self):
        """Length attribute"""
        return len(self.parsed_data)

    def __add__(self, parser):
        """Join two parsers together"""
        return CombinedParser(self, parser)

class CombinedParser(Parser):

    def __init__(self, parser1, parser2):
        """Constructor for CombinedParser"""

        self.parser1 = parser1
        self.parser2 = parser2

    def __iter__(self):
        """Combine iterators from the two parsers"""
        return chain(self.parser1, self.parser2)

    def __len__(self):
        """Total length is the sum of both iterators"""
        return len(self.parser1) + len(self.parser2)

class GuidedParser(Parser):

    def __init__(self, path_template, loader, parameters):
        """Constructor for the GuidedParser"""
        super(GuidedParser, self).__init__()
        self.path_template = path_template
        self.loader = loader
        self.collect = inspect.getargspec(loader).args[1:]
        self.parameters = parameters

    def populate(self):
        """Populate the parser using the data on the specified paths"""

        params_copy = self.parameters.copy()        
        collect_params = {}
        path_template_copy = self.path_template
        # First the path template needs to be reformatted if there are variables
        # to collect
        if self.collect:
            for param in self.collect:
                collect_params[param] = params_copy.pop(param)
                path_template_copy = re.sub('{{ *{} *}}'.format(param),
                                            '{{{{{}}}}}'.format(param),
                                            path_template_copy)

        # Now go through all non-collected parameters and set up FileWrapper for each
        for values in product(*params_copy.values()):
            paramdict = dict(zip(params_copy.keys(), values))
            sub_template = path_template_copy.format(**paramdict)

            timestamps = []
            for collected_values in product(*collect_params.values()):
                collected_paramsdict = dict(zip(collect_params.keys(),
                                                collected_values))
                filename = sub_template.format(**collected_paramsdict)
                timestamps.append(os.path.getmtime(filename))
            timestamp = max(timestamps)
            def wrapped_loader(template):
                return self.loader(template, **collect_params)
            filewrapper = FileWrapper(sub_template, wrapped_loader,
                                      timestamp=timestamp)
            filewrapper.params = paramdict
            self.parsed_data.append(filewrapper)

        self.populated = True
