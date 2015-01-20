from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict, namedtuple
import inspect
from itertools import product
import logging
import os

from anflow.config import Config
from anflow.data import DataSet, Datum, Query
from anflow.utils import get_root_path, get_dependency_files


Model = namedtuple("Model", ("func", "input_tag", "path_template"))
View = namedtuple("View", ("func", "input_tags", "output_dir"))


def gather_function_args(func):
    """Gathers function arguments and defaults"""
    # TODO: Add test
    working_func = getattr(func, "original", func)
    argspec = inspect.getargspec(working_func)
    # Omit first argument - this is data
    args = dict([(arg, None) for arg in argspec.args[1:]])
    error_name = getattr(func, "error_name", None)
    if error_name:
        args.pop(error_name)
    if argspec.defaults:
        defaults = dict(zip(argspec.args[::-1], argspec.defaults[::-1]))
        args.update(defaults)
    return args


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
        self.parsers = OrderedDict()
        self.models = OrderedDict()
        self.views = OrderedDict()
        self.results = OrderedDict()
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

    def register_parser(self, tag, parser):
        """Register the supplied parser with the specified tag"""
        self.parsers[tag] = parser

    def register_model(self, model_tag, func, input_tag, path_template=None):
        """Register the supplied model function and associated parameters"""
        self.models[model_tag] = Model(func, input_tag, path_template)

    def register_view(self, view_tag, func, input_tags, output_dir=None):
        """Returns a decorator to register the designated view"""
        # Adapt this so it's not a decorator
        self.views[view_tag] = View(func, input_tags, output_dir)

    def run_model(self, model, force=False, dry_run=False):
        """Run a model"""

        self._setup_log()

        log = self.log.getChild('models.{}'.format(model))
        log.info("Preparing to run model {}".format(model))

        func, data, parameters, query, path_template = self.models[model]
        try:
            argspec = inspect.getargspec(func.original)
        except AttributeError:
            argspec = inspect.getargspec(func)
        args = argspec.args[1:]
        try:
            if func.error_name:
                args.remove(func.error_name)
        except AttributeError:
            pass
        if argspec.defaults:
            defaults = dict(zip(argspec.args[::-1], argspec.defaults[::-1]))
        else:
            defaults = {}
        parameters = parameters or [{}]
        query = query or Query()
        results_dir = os.path.join(self.config.RESULTS_DIR,
                                   model)
        if path_template:
            path_template = os.path.join(model, path_template)
        try:
            os.makedirs(results_dir)
        except OSError:
            pass

        # TODO: Remove this
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

        # TODO: Remove this if statement
        if do_run:
            log.info("Running model")
            num_runs = len(data) * len(parameters)
            for i, (datum, params) in enumerate(product(data, parameters)):
                if not query.evaluate([datum.params]):
                    # If query filters out the datum parameters, skip
                    continue
                joint_params = {}
                joint_params.update(datum.params)
                joint_params.update(params)
                kwargs = {}
                for key in args:
                    try:
                        kwargs[key] = joint_params[key]
                    except KeyError:
                        kwargs[key] = defaults[key]
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

        func, models, parameters, query = self.views[view]
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
            # TODO: Get rid of this. Run always
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
            query = query or Query()
            for params in parameters:
                data = {}
                # Iterate through the input models and compile a dictionary
                # of input data
                for model in models:
                    # Get model parameter names
                    # Get the result of the filter
                    result = model.results.filter(query, **params)
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
        for func, input_data, params, query, template in self.models.values():
            try:
                dependency = input_data._parent.simulation
            except AttributeError:
                pass
            else:
                if dependency != self:
                    simulations.append(dependency)

        return simulations
