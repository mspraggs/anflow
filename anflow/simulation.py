from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import inspect
from itertools import product
import logging
import os

from anflow.config import Config
from anflow.data import DataSet, Datum
from anflow.utils import get_root_path, get_dependency_files


class Simulation(object):
    defaults = {'DEBUG': False,
                'LOGGING_LEVEL': logging.NOTSET,
                'LOGGING_CONSOLE': True,
                'LOGGING_FORMAT': "%(asctime)s : %(name)s : %(levelname)s : %(message)s",
                'LOGGING_DATEFMT': "%d/%m/%Y %H:%M:%S",
                'LOGGING_FILE': None}

    def __init__(self, import_name, root_path=None):
        """Constructor"""

        self.config = Config()
        self.models = OrderedDict()
        self.views = OrderedDict()
        self.import_name = import_name

        self.root_path = root_path or get_root_path(import_name)

        self.config.from_dict(self.defaults)
        # Set up the log
        self.log = logging.getLogger(import_name)
        formatter = logging.Formatter(self.config.LOGGING_FORMAT,
                                      self.config.LOGGING_DATEFMT)
        if self.config.LOGGING_CONSOLE:
            ch = logging.StreamHandler()
            ch.setLevel(self.config.LOGGING_LEVEL)
            ch.setFormatter(formatter)
            self.log.addHandler(ch)
        if self.config.LOGGING_FILE:
            fh = logging.FileHandler(self.config.LOGGING_FILE)
            fh.setLevel(self.config.LOGGING_LEVEL)
            fh.setFormatter(formatter)
            self.log.addHandler(fh)

    def register_model(self, input_data, parameters=None):
        """Register the supplied model function and associated parameters"""

        try:
            data_params = input_data._params
        except AttributeError:
            data_params = [datum.params for datum in input_data]
        actual_parameters = parameters or [{}]

        def decorator(func):
            try:
                funcname = func.__name__
            except AttributeError:
                funcname = func.original.__name__
            self.models[funcname] = (func, input_data, parameters)
            prefix = "{}_".format(funcname)
            all_params = []
            for dparams in data_params:
                for params in actual_parameters:
                    temp_params = {}
                    temp_params.update(dparams)
                    temp_params.update(params)
                    all_params.append(temp_params)
            func.results = DataSet(all_params, self.config,
                                   prefix)
            func.results._parent = func
            return func

        return decorator

    def register_view(self, models, parameters=None):
        """Returns a decorator to register the designated view"""

        def decorator(func):
            self.views[func.__name__] = (func, models, parameters)
            return func

        return decorator

    def run_model(self, model, force=False):
        """Run a model"""

        log = self.log.getChild('model.{}'.format(model))
        log.info("Preparing to run model {}".format(model))

        func, data, parameters = self.models[model]
        try:
            args = inspect.getargspec(func.original).args[1:]
            if func.error_name:
                args.remove(func.error_name)
        except AttributeError:
            args = inspect.getargspec(func).args[1:]
        parameters = parameters or [{}]
        file_prefix = os.path.join(self.config.RESULTS_DIR,
                                   model + "_")
        try:
            os.makedirs(self.config.RESULTS_DIR)
        except OSError:
            pass

        # Determine whether data is up to date and we should run the model
        # Part of this is concerned with determining if source has changed
        if force:
            log.info("Model run has been forced")
            do_run = force
        else:
            log.info("Checking whether results are up-to-date")
            source_files = get_dependency_files(func, self.root_path)
            try:
                source_timestamp = max(map(os.path.getmtime, source_files))
            except ValueError:
                source_timestamp = 0
            input_timestamp = max([datum.timestamp for datum in data])
            results = self.models[model][0].results
            try:
                results = results.all()
            except IOError:
                results = []
            if not results:  # Check for lack of existing results
                do_run = True
            else:
                results_timestamp = min([result.timestamp for result in results])
                # Check for new input or source code
                do_run = not (results_timestamp > input_timestamp and
                              results_timestamp > source_timestamp)

        if do_run:
            log.info("Running model")
            num_runs = len(data) * len(parameters)
            for i, (datum, params) in enumerate(product(data, parameters)):
                joint_params = {}
                joint_params.update(datum.params)
                joint_params.update(params)
                kwargs = dict([(key, joint_params[key]) for key in args])
                log.info("Running model with parameters ({} of {}):"
                         .format(i + 1, num_runs))
                for key, value in kwargs.items():
                    log.info("{}: {}".format(key, value))
                if hasattr(func, 'resampled'):
                    result = func(datum, **kwargs)
                else:
                    result = func(datum.data, **kwargs)
                if result is not None:
                    log.info("Saving results")
                    result_datum = Datum(joint_params, result, file_prefix)
                    result_datum.save()

        return do_run

    def run_view(self, view, force=False):
        """Runs the specified view"""

        log = self.log.getChild("view.{}".format(view))
        log.info("Preparing to run view {}".format(view))

        func, models, parameters = self.views[view]
        args = inspect.getargspec(func).args[1:]
        reports_dir = self.config.REPORTS_DIR
        try:
            os.makedirs(reports_dir)
        except OSError:
            pass

        if force:
            log.info("View run has been forced")
            do_run = force
        else:
            # Determine whether we need to run the view
            log.info("Checking whether output is up-to-date")
            source_files = get_dependency_files(func, self.root_path)
            try:
                source_timestamp = max(map(os.path.getmtime, source_files))
            except ValueError:
                source_timestamp = 0
            input_timestamp = 0
            for model in models:
                candidate = max([datum.timestamp for datum in model.results])
                input_timestamp = max(candidate, input_timestamp)
            try:
                timestamp_path = os.path.join(reports_dir,
                                              "{}.run".format(view))
                last_run_timestamp = os.path.getmtime(timestamp_path)
            except OSError:
                do_run = True
            else:
                do_run = (last_run_timestamp < input_timestamp
                          or last_run_timestamp < source_timestamp)

        if do_run:
            log.info("Running view")
            old_cwd = os.getcwd()
            os.chdir(self.config.REPORTS_DIR)
            parameters = parameters or [{}]
            for params in parameters:
                data = {}
                # Iterate through the input models and compile a dictionary
                # of input data
                for model in models:
                    # Get model parameter names
                    param_names = model.results.first()._params
                    # Construct filter with parameters relevant to model
                    model_filter = dict([(key, value)
                                         for key, value in params.items()
                                         if key.split("__")[0] in param_names])
                    # Get the result of the filter
                    result = model.results.filter(**model_filter).all()
                    # Assign the result to the data dictionary
                    data[model.__name__] = result
                kwargs = dict([(arg, params[arg]) for arg in args])
                log.info("Running view with parameters:")
                for key, value in kwargs.items():
                    log.info("{}: {}".format(key, value))
                func(data, **kwargs)
            with open("{}.run".format(view), 'w') as f:
                pass
            os.chdir(old_cwd)

        return do_run

    def run(self, force=False):
        """Run all models in this simulation"""

        self.log.info("Running all models and views")
        results = {}
        for model in self.models.keys():
            results[model] = self.run_model(model, force)
        for view in self.views.keys():
            results[view] = self.run_view(view, force)

        return results
