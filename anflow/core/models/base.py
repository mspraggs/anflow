from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
from functools import partial

class Model(object):

    main = None
    parser = None
    resampler = None
    parameters = None

    def __init__(self):
        """Set up empty results list"""

        self.results = []

    def run(self, *args, **kwargs):
        """Runs the measurement on the files returned by the specified parser"""

        print(parser.populate())
        main_partial = partial(self.main, *args, **kwargs)
        
        for params, data in self.parser:
            # Combine parameters
            argspec = inspect.getargspec(self.main)
            all_params = dict(zip(argspec.args, args))
            all_params.update(kwargs)

            if self.resampler:
                result = self.resampler.run(data, main_partial)
            else:
                result = main_partial(data)

            self.results.append((all_params, results))

    def save(self, result, params):
        """Saves the result defined by the specified parameters"""

        for params, result in self.results:
            pass # do something
