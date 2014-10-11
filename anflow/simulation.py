from __future__ import absolute_import

from collections import OrderedDict
import inspect
from itertools import product
import os

from anflow.config import Config
from anflow.data import DataSet, Datum



class Simulation(object):

    def __init__(self):
        """Constructor"""

        self.config = Config()
        self.models = OrderedDict()

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

    def run_model(self, model, force=False):
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

        # Determine whether data is up to date and we should run the model
        input_timestamp = max([datum.timestamp for datum in data])
        results = self.models[model][0].results
        try:
            results = results.all()
        except IOError:
            results = []
        if not results: # Check for lack of existing results
            do_run = True
        else:
            results_timestamp = min([result.timestamp for result in results])
            if results_timestamp > input_timestamp: # Check for new input
                do_run = False
            else:
                do_run = True
        # Apply override if required
        do_run = force if force else do_run

        if do_run:
            for datum, params in product(data, parameters):
                joint_params = {}
                joint_params.update(datum.params)
                joint_params.update(params)
                kwargs = dict([(key, joint_params[key]) for key in args])
                result = func(datum.data, **kwargs)
                result_datum = Datum(joint_params, result, file_prefix)
                result_datum.save()

        return do_run

    def run(self, force=False):
        """Run all models in this simulation"""

        results = {}
        for model in self.models.keys():
            results[model] = self.run_model(model, force)

        return results
