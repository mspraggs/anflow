from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict, namedtuple
import inspect
from itertools import product
import logging
import os

from anflow.config import Config
from anflow.data import DataSet, Datum, Query, generate_filename
from anflow.utils import get_root_path, get_dependency_files


Model = namedtuple("Model", ("func", "input_tag", "path_template", "load_only"))
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

    def _get_input(self, tag):
        """Look in parsers for the specified input tag, and if it's not there
        then look in results"""
        # TODO: Add test
        value = self.parsers.get(tag, self.results.get(tag))
        if value is None:
            raise KeyError("Tag {} does not exist".format(tag))
        return value

    def register_parser(self, tag, parser):
        """Register the supplied parser with the specified tag"""
        self.parsers[tag] = parser

    def register_model(self, model_tag, func, input_tag, path_template=None,
                       load_only=False):
        """Register the supplied model function and associated parameters"""
        self.models[model_tag] = Model(func, input_tag, path_template,
                                       load_only)

    def register_view(self, view_tag, func, input_tags, output_dir=None):
        """Returns a decorator to register the designated view"""
        # Adapt this so it's not a decorator
        self.views[view_tag] = View(func, input_tags, output_dir)

    def run_model(self, model_tag, parameters=None, query=None, dry_run=False):
        """Run a model"""

        self._setup_log()
        log = self.log.getChild('models.{}'.format(model_tag))
        log.info("Preparing to run model {}".format(model_tag))

        func, input_tag, path_template, load_only = self.models[model_tag]
        parameters = parameters or [{}]
        query = query or Query()

        data = self._get_input(input_tag)
        args = gather_function_args(func)

        results_dir = os.path.join(self.config.RESULTS_DIR,
                                   model_tag)
        if path_template:
            path_template = os.path.join(model_tag, path_template)
        try:
            os.makedirs(results_dir)
        except OSError:
            pass

        log.info("Running model")
        num_runs = len(data) * len(parameters)
        dataset_params = []
        for i, (datum, params) in enumerate(product(data, parameters)):
            if not query.evaluate([datum.params]):
                # If query filters out the datum parameters, skip
                continue
            # Construct the function arguments from the given parameters
            joint_params = datum.params.copy()
            joint_params.update(params)
            # Retrieve values, falling back to defaults where they exist
            kwargs = dict([(key, joint_params.get(key, args[key]))
                           for key in args.keys()])

            log.info("Running model ({} of {}):"
                     .format(i + 1, num_runs))
            for key, value in joint_params.items():
                log.info("{}: {}".format(key, value))
            if load_only:
                dataset_params.append(joint_params)
            else:
                # TODO: Fix this in accordance with resampler config
                if hasattr(func, 'resampled'):
                    result = func(datum, **kwargs)
                else:
                    result = func(datum.data, **kwargs)
                if result is not None:
                    dataset_params.append(joint_params)
                    if not dry_run:
                        log.info("Saving results")
                        result_datum = Datum(joint_params, result,
                                             results_dir + "/",
                                             path_template)
                        result_datum.save()
                elif not dry_run:
                    log.info("Dry run, so no results saved")

        self.results[model_tag] = DataSet(dataset_params, self.config,
                                          results_dir + "/", path_template)

    def run_view(self, view_tag, parameters=None, queries=None):
        """Runs the specified view"""

        self._setup_log()
        log = self.log.getChild("view.{}".format(view_tag))
        log.info("Preparing to run view {}".format(view_tag))

        func, input_tags, output_dir = self.views[view_tag]
        parameters = parameters or [{}]
        queries = queries or Query()
        if type(queries) != dict:
            queries = dict([(tag, queries) for tag in input_tags])

        args = gather_function_args(func)
        reports_dir = output_dir or os.path.join(self.config.REPORTS_DIR,
                                                 view_tag)
        try:
            os.makedirs(reports_dir)
        except OSError:
            pass

        log.info("Running view")
        old_cwd = os.getcwd()
        os.chdir(reports_dir)
        for params in parameters:
            data = {}
            # Iterate through the input models and compile a dictionary
            # of input data
            for input_tag in input_tags:
                # Apply relevant filters
                query = queries[input_tag] or Query()
                result = self.results[input_tag].filter(query, **params)
                # Assign the result to the data dictionary
                data[input_tag] = result
            kwargs = dict([(key, params.get(key, args[key]))
                           for key in args.keys()])
            if len(params) > 0:
                log.info("Running view with parameters:")
                for key, value in params.items():
                    log.info("{}: {}".format(key, value))
            else:
                log.info("Running view without parameters")
            func(data, **kwargs)
        os.chdir(old_cwd)
