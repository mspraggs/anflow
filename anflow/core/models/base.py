from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
from functools import partial



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

        self.results_format_args = re.findall(r'\{ * (\w+) *\}',
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
            pass # do something
