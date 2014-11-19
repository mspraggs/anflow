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
        self.log = logging.getLogger(self.import_name)
        self._setup_log()

    def _setup_log(self):
        # Set up the log
        log = logging.getLogger()
        log.handlers = []
        log.setLevel(self.config.LOGGING_LEVEL)
        formatter = logging.Formatter(self.config.LOGGING_FORMAT,
                                      self.config.LOGGING_DATEFMT)
        if self.config.LOGGING_CONSOLE:
            ch = logging.StreamHandler()
            ch.setLevel(self.config.LOGGING_LEVEL)
            ch.setFormatter(formatter)
            log.addHandler(ch)
        if self.config.LOGGING_FILE:
            fh = logging.FileHandler(self.config.LOGGING_FILE)
            fh.setLevel(self.config.LOGGING_LEVEL)
            fh.setFormatter(formatter)
            log.addHandler(fh)

    def register_model(self, input_data, parameters=None, path_template=None):
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
            local_path_template = path_template
            if local_path_template:
                local_path_template = os.path.join(funcname, local_path_template)
            self.models[funcname] = (func, input_data, parameters, local_path_template)
            prefix = "{}/".format(funcname)
            all_params = []
            for dparams in data_params:
                for params in actual_parameters:
                    temp_params = {}
                    temp_params.update(dparams)
                    temp_params.update(params)
                    all_params.append(temp_params)
            func.results = DataSet(all_params, self.config,
                                   prefix, path_template)
            func.results._parent = func
            func.simulation = self
            return func

        return decorator

    def register_view(self, models, parameters=None):
        """Returns a decorator to register the designated view"""

        def decorator(func):
            self.views[func.__name__] = (func, models, parameters)
            return func

        return decorator

    def run_model(self, model, force=False, dry_run=False):
        """Run a model"""

        self._setup_log()

        log = self.log.getChild('models.{}'.format(model))
        log.info("Preparing to run model {}".format(model))

        func, data, parameters, path_template = self.models[model]
        try:
            args = inspect.getargspec(func.original).args[1:]
            if func.error_name:
                args.remove(func.error_name)
        except AttributeError:
            args = inspect.getargspec(func).args[1:]
        parameters = parameters or [{}]
        results_dir = os.path.join(self.config.RESULTS_DIR,
                                   model)
        if path_template:
            path_template = os.path.join(model, path_template)
        try:
            os.makedirs(results_dir)
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
            results = func.results
            try:
                results = results.all()
            except IOError:
                results = []
            if not results:  # Check for lack of existing results
                log.info("No results for model")
                do_run = True
            else:
                results_timestamp = min([result.timestamp for result in results])
                if results_timestamp < input_timestamp:
                    log.info("Input data is newer than results")
                if results_timestamp < source_timestamp:
                    log.info("Model source is newer than results")
                # Check for new input or source code
                do_run = (results_timestamp < input_timestamp or
                          results_timestamp < source_timestamp)

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
                for key, value in joint_params.items():
                    log.info("{}: {}".format(key, value))
                if hasattr(func, 'resampled'):
                    result = func(datum, **kwargs)
                else:
                    result = func(datum.data, **kwargs)
                if result is not None and not dry_run:
                    log.info("Saving results")
                    result_datum = Datum(joint_params, result, results_dir + "/",
                                         path_template)
                    result_datum.save()
                elif not dry_run:
                    log.info("Dry run, so no results saved")
        else:
            log.info("Results are up-to-date")

        return do_run

    def run_view(self, view, force=False):
        """Runs the specified view"""

        self._setup_log()
        log = self.log.getChild("view.{}".format(view))
        log.info("Preparing to run view {}".format(view))

        func, models, parameters = self.views[view]
        args = inspect.getargspec(func).args[1:]
        reports_dir = os.path.join(self.config.REPORTS_DIR, view)
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
                timestamp_path = os.path.join(self.config.REPORTS_DIR,
                                              "{}.run".format(view))
                last_run_timestamp = os.path.getmtime(timestamp_path)
            except OSError:
                log.info("View has not been run")
                do_run = True
            else:
                if last_run_timestamp < input_timestamp:
                    log.info("Input data is newer than view output")
                if last_run_timestamp < source_timestamp:
                    log.info("View source code is newer than view output")
                do_run = (last_run_timestamp < input_timestamp
                          or last_run_timestamp < source_timestamp)

        if do_run:
            log.info("Running view")
            old_cwd = os.getcwd()
            os.chdir(reports_dir)
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
                if len(parameters) > 0:
                    log.info("Running view with parameters:")
                    for key, value in params.items():
                        log.info("{}: {}".format(key, value))
                else:
                    log.info("Running view without parameters")
                func(data, **kwargs)
            os.chdir(old_cwd)
            with open(os.path.join(self.config.REPORTS_DIR,
                                   "{}.run".format(view)), 'w'):
                pass
        else:
            log.info("View output is up-to-date")

        return do_run

    def run(self, force=False, dry_run=False):
        """Run all models in this simulation"""

        self.log.info("Running all models and views")
        results = {}
        for model in self.models.keys():
            results[model] = self.run_model(model, force, dry_run)
        for view in self.views.keys():
            results[view] = self.run_view(view, force)

        return results

    @property
    def dependencies(self):
        """Retrieve a list of simulations on which this depends"""

        simulations = []
        for func, input_data, params, template in self.models.values():
            try:
                dependency = input_data._parent.simulation
            except AttributeError:
                pass
            else:
                if dependency != self:
                    simulations.append(dependency)

        return simulations