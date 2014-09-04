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
from anflow.utils import get_study
from anflow.utils.io import projectify



class MetaModel(type):
    # Meta class to create static data member for Model
    def __new__(cls, names, bases, attrs):
        try:
            attrs['abstract']
        except KeyError as e:
            debug_message(e)
            attrs['abstract'] = False
        new_class = super(MetaModel, cls).__new__(cls, names, bases, attrs)
        return MetaModel.reload(new_class)
    
    def reload(cls):
        new_class = cls
        if new_class.abstract:
            return new_class

        study = get_study(new_class.__module__)
        # Fail if we're not looking at a class that's in a study
        if not new_class.results_format or study not in settings.ACTIVE_STUDIES:
            return new_class
        
        results = DataSet()            
        results_dir = projectify(settings.RESULTS_TEMPLATE
                                 .format(study_name=study))
        results_regex = re.compile(re.sub(r'\{ *(?P<var>\w+) *\}',
                                          '(?P<\g<var>>.+)',
                                          new_class.results_format))
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

    abstract = False
    main = None # The function that encapsulates the model behaviour
    input_stream = None # The raw data to feed into the model
    parameters = None # A list of additional parameters to feed the model
    results_format = None # The template for the model filename
    depends_on = None # A list of models this model depends on
    resampler = None # The resampler object that'll do the resampling

    def __init__(self):
        """Set up empty results list"""
        self.new_results = DataSet()

        self.mainargspec = inspect.getargspec(self.main)
        if not self.results_format:
            try:
                self.results_format = self.input_stream.path_format
            except AttributeError as e:
                debug_message(e)
                raise AttributeError("Member results_format not specified and "
                                     "input_stream has no member path_format")

        self.study_name = get_study(self.__module__)

    def run(self, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        for datum in self.input_stream:
            # Convert parsed to types indicated by parameters
            for key in datum.paramsdict().keys():
                param_type = getattr(self, key)
                setattr(datum, key, param_type(getattr(datum, key)))
            # Combine parameters
            all_params = dict(zip(self.mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(datum.paramsdict())
            main_partial = partial(self.main, **all_params)

            if self.resampler:
                results = self.resampler(datum, main_partial)
                result = results[0]
                centre = results[1]
                try:
                    error = results[2]
                except IndexError as e:
                    debug_message(e)
            else:
                result = main_partial(datum.value)
                
            filename = os.path.join(settings.RESULTS_TEMPLATE
                                    .format(study_name=self.study_name),
                                    self.results_format.format(**all_params))
            new_datum = Datum(all_params, result, projectify(filename))
            try:
                new_datum.central_value = centre
                new_datum.error = error
            except NameError as e:
                debug_message(e)

            self.new_results.append(new_datum)

    def save(self):
        """Saves the result defined by the specified parameters"""
        self.new_results.save()
