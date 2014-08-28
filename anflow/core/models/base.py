from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect
import re
try:
    import cPickle as pickle
except ImportError:
    import pickle
from functools import partial

from anflow.conf import settings
from anflow.utils.debug import debug_message

class Model(object):

    main = None
    input_stream = None
    resampler = None
    parameters = None
    results_format = None

    def __init__(self):
        """Set up empty results list"""
        self.results = []

        self.mainargspec = inspect.getargspec(self.main)
        self.main_has_args = (True
                              if self.mainargspec.args
                              or self.mainargspec.varargs
                              or self.mainargspec.keywords
                              else False)
        if not self.results_format:
            try:
                self.results_format = self.input_stream.path_format
            except AttributeError as e:
                debug_message(e)
                raise AttributeError("Member results_format not specified and "
                                     "input_stream has no member path_format")

        self.results_format_args = re.findall(r'\{ *(\w+) *\}',
                                              self.results_format)

    def run(self, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        main_partial = partial(self.main, *args, **kwargs)
        
        for params, data in self.input_stream:
            # Combine parameters
            all_params = dict(zip(self.mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(params)

            if self.resampler:
                result = self.resampler.run(data, main_partial)
            else:
                result = main_partial(data)

            self.results.append((all_params, result))

    def save(self):
        """Saves the result defined by the specified parameters"""

        
        for params, result in self.results:
            # Parameters missing from self.results_format
            missing_params = dict([(key, val) for key, val in params.items()
                                   if key not in self.results_format_args])

            study_name = self.__module__.split('.')[0]
            filename = os.path.join(settings.RESULTS_TEMPLATE
                                    .format(study_name=study_name),
                                    self.results_format.format(**params))
            if self.main_has_args and missing_params:
                filename, extension = os.path.splitext(filename)
                for key, val in missing_params.items():
                    filename += "_{}{}".format(key, val)
                filename += extension
                
            with open(filename, 'w') as f:
                pickle.dump(result, f)
