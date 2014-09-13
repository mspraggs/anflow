from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argparse import ArgumentParser
from itertools import product
import importlib
import imp
import sys

from anflow.conf import settings
from anflow.db.models import Model
from anflow.utils.debug import debug_message
from anflow.utils.logging import logger

def run_model(model_class, models_run, run_dependencies=True):
    """Recursively run a model and its dependencies, returning a list of the
    models run"""
    log = logger()
    log.info("Preparing to run model {}".format(model_class.__name__))
    my_models_run = []
    if model_class.depends_on and run_dependencies:
        log.info("Running model {} dependencies".format(model_class.__name__))
        for dependency in model_class.depends_on:
            if dependency not in models_run + my_models_run:
                my_models_run.extend(run_model(dependency, my_models_run,
                                               run_dependencies))

    log.info("Initialising model")
    # We need to reload the model module to update any input_data parameters
    module = importlib.import_module(model_class.__module__)
    module = imp.reload(module)
    old_model_class = model_class
    model_class = getattr(module, model_class.__name__)
    model = model_class()
    try:
        model.input_stream.populate()
    except AttributeError as e:
        debug_message(e)
    if model.parameters:
        for params in model.parameters:
            log.info("Running model {} with following parameters:"
                     .format(model.__class__.__name__))
            for key, value in params.items():
                log.info("{}: {}".format(key, value))
            try:
                model.run(*params[0], **params[1])
            except (IndexError, KeyError, TypeError) as e:
                debug_message(e)
            try:
                model.run(**params)
            except TypeError as e:
                debug_message(e)
                model.run(*params)

            log.info("Finished this {} parameter run"
                     .format(model.__class__.__name__))
    else:
        log.info("Running model {} without parameters"
                 .format(model.__class__.__name__))
        model.run()
        log.info("Finished running {} without parameters"
                 .format(model.__class__.__name__))
    log.info("Finished running model {}".format(model.__class__.__name__))
    log.info("Saving model results")
    model.save()

    log.info("Loading results back into model")
    my_models_run.append(old_model_class)
    return my_models_run

def main(argv):

    # TODO: Some arguments here to filter models, studies,
    # override running of dependencies, etc.

    log = logger()

    parser = ArgumentParser()
    parser.add_argument('--study', dest='study', action='store',
                        default=None)
    parser.add_argument('--component', dest='component', action='store',
                        default=None)
    parser.add_argument('--dependencies', dest='run_dependencies',
                        action='store_true')
    parser.add_argument('--no-dependencies', dest='run_dependencies',
                        action='store_false')
    parser.set_defaults(run_dependencies=True)
    args = parser.parse_args(argv)
    if args.study:
        studies = [args.study]
    else:
        studies = settings.ACTIVE_STUDIES
    if not args.component:
        run_models = run_views = True
    else:
        run_models = args.component == 'models'
        run_views = args.component == 'views'
    
    models = []
    views = []
    log.info("Gathering models")
    for study in studies:
        module_name = (settings.COMPONENT_TEMPLATE
                       .format(component='models', study_name=study)
                       .replace('/', '.'))
        module = importlib.import_module(module_name)
        for name in dir(module):
            member = getattr(module, name)
            try:
                if issubclass(member, Model):
                    if not member.abstract and member.__module__ == module_name:
                        log.info("Adding model {} in study {}"
                                 .format(member.__name__, study))
                        models.append(member)
            except TypeError as e:
                debug_message(e)
                
    for study in studies:
        module = importlib.import_module(settings.COMPONENT_TEMPLATE
                                         .format(component='views',
                                                 study_name=study)
                               .replace('/', '.'))
        new_views = module.view_functions
        for view in new_views:
            try: # Get the name if it's a real function
                view_name = view.__name__
            except AttributeError: # Or the function name if partial's been used
                view_name = view.func.__name__
            log.info("Adding view {} in study {}"
                     .format(view_name, study))
        views.extend(new_views)

    models_run = []
    if run_models:
        while len(models) > 0:
            new_models_run = run_model(models[0], models_run,
                                       args.run_dependencies)
            for model in new_models_run:
                models.remove(model)
            models_run.extend(new_models_run)

    # Might need to reload models here to get the latest data
    if run_views:
        for view in views:
            try:
                log.info("Running view {}".format(view.__name__))
            except AttributeError:
                log.info("Running view {}".format(view.func.__name__))
            view()
