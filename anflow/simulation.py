from __future__ import absolute_import

import inspect
from itertools import product
import os

from anflow.config import Config
from anflow.data import DataSet, Datum



class Simulation(object):

    def __init__(self):
        """Constructor"""

        self.config = Config()
        self.models = {}

    def register_model(self, input_data, parameters=None):
        """Register the supplied model function and associated parameters"""

        try:
            data_params = input_data._params
        except AttributeError:
            data_params = [datum.params for datum in input_data]
        actual_parameters = parameters or [{}]

        def decorator(func):
            self.models[func.__name__] = (func, input_data, parameters)
            prefix = os.path.join(self.config.RESULTS_DIR,
                                  "{}_".format(func.__name__))
            all_params = []
            for dparams in data_params:
                for params in actual_parameters:
                    temp_params = {}
                    temp_params.update(dparams)
                    temp_params.update(params)
                    all_params.append(temp_params)
            func.results = DataSet(all_params,
                                   os.path.join(self.config.RESULTS_DIR,
                                                prefix))
            func.results._parent = func
            return func
        return decorator

    def run_model(self, model):
        """Run a model"""

        func, data, parameters = self.models[model]
        args = inspect.getargspec(func).args[1:]
        parameters = parameters or [{}]
        file_prefix = os.path.join(self.config.RESULTS_DIR,
                                   model + "_")
        try:
            os.makedirs(self.config.RESULTS_DIR)
        except OSError:
            pass        
        for datum, params in product(data, parameters):
            joint_params = {}
            joint_params.update(datum.params)
            joint_params.update(params)
            kwargs = dict([(key, joint_params[key]) for key in args])
            result = func(datum.data, **kwargs)
            result_datum = Datum(joint_params, result, file_prefix)
            result_datum.save()
