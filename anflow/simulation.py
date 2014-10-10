from __future__ import absolute_import

from anflow.config import Config
from anflow.data import gather_data



class Simulation(object):

    def __init__(self):
        """Constructor"""

        self.config = Config()
        self.models = {}

    def register_model(self, input_data, parameters=None):
        """Register the supplied model function and associated parameters"""

        data_params = [datum.params for datum in input_data]

        def decorator(func):
            self.models[func.__name__] = (func, input_data, parameters)
            prefix = "{}_".format(func.__name__)
            func.results = gather_data(self.config.RESULTS_DIR,
                                       data_params, prefix, parameters)
            func.results._parent = func
            return func
        return decorator

    def run_model(self, model):
        """Run a model"""
