from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect
import re
from functools import partial

from anflow.conf import settings
from anflow.core.data import Datum, DataSet
from anflow.utils.debug import debug_message



class MetaModel(type):
    # Meta class to create static data member for Model
    def __new__(cls, names, bases, attrs):
        new_class = super(MetaModel, cls).__new__(cls, names, bases, attrs)
        study = attrs['__module__'].split('.')[0]
        # Fail if we're not looking at a class that's in a study
        if not attrs['results_format'] or study not in settings.ACTIVE_STUDIES:
            return new_class
        
        results = DataSet()            
        results_dir = settings.RESULTS_TEMPLATE.format(study_name=study)
        results_regex = re.compile(re.sub(r'\{ *(?P<var>\w+) *\}',
                                          '(?P<\g<var>>.+)',
                                          attrs['results_format']))
        # Loop through results and gather data and parameters
        for directory, dirs, files in os.walk(results_dir):
            for f in files:
                path = os.path.join(directory, f)
                if results_regex.search(path):
                    results.append(Datum.load(path))
        new_class.data = results
        return new_class

class Model(object):

    __metaclass__ = MetaModel
    
    main = None
    input_stream = None
    resampler = None
    parameters = None
    results_format = None
    depends_on = None

    def __init__(self):
        """Set up empty results list"""
        self.new_results = DataSet()

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
        self.study_name = self.__module__.split('.')[0]

    def run(self, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        main_partial = partial(self.main, *args, **kwargs)
        for datum in self.input_stream:
            # Combine parameters
            all_params = dict(zip(self.mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(datum.paramsdict())

            for key, value in all_params.items():
                all_params[key] = getattr(self, key)(value)

            if self.resampler:
                result = self.resampler.run(datum.value, main_partial)
            else:
                result = main_partial(datum.value)
                
            filename = os.path.join(settings.RESULTS_TEMPLATE
                                    .format(study_name=self.study_name),
                                    self.results_format.format(**all_params))

            self.new_results.append(Datum(all_params, result, filename))

    def save(self):
        """Saves the result defined by the specified parameters"""
        self.new_results.save()
