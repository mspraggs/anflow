from __future__ import absolute_import

from anflow.config import Config
from anflow.data import Datum



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
