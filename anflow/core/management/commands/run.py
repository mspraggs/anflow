from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argparse import ArgumentParser
from datetime import datetime
from itertools import product
import importlib
import imp
import os
import sys

from anflow.conf import settings
from anflow.db.models import Model
from anflow.db.history import History
from anflow.utils.debug import debug_message
from anflow.utils.logging import logger



def set_term_handler(func):

    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = '.'.join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python {}"
                            .format(version))
    else:
        import signal
        signal.signal(signal.SIGTERM, func)

def cleanup(model_classes, start_time):
    log = logger()
    log.info("Cleaning up ")
    for model_class in model_classes:
        model_class.data.filter(timestamp__gte=start_time).delete()

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
    old_model_class = model_class
    try:
        model_class.input_stream.populate()
    except AttributeError as e:
        debug_message(e)
    if model_class.parameters:
        for params in model_class.parameters:
            log.info("Running model {} with following parameters:"
                     .format(model_class.__name__))
            for key, value in params.items():
                log.info("{}: {}".format(key, value))
            try:
                models = model_class.run(*params[0], **params[1])
            except (IndexError, KeyError, TypeError) as e:
                debug_message(e)
            try:
                models = model_class.run(**params)
            except TypeError as e:
                debug_message(e)
                models = model_class.run(*params)

            log.info("Finished this {} parameter run"
                     .format(model_class.__name__))
            log.info("Saving results for this run")
            for model in models:
                model.save()
    else:
        log.info("Running model {} without parameters"
                 .format(model_class.__name__))
        models = model_class.run()
        log.info("Finished running {} without parameters"
                 .format(model_class.__name__))
        log.info("Saving results")
        for model in models:
            model.save()
    log.info("Finished running model {}".format(model_class.__name__))
    log.info("Saving model results")

    log.info("Loading results back into model")
    my_models_run.append(model_class)
    return my_models_run

def main(argv):

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

    start = datetime.now()
    
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

    set_term_handler(lambda: cleanup(models, start))
                
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
    models_to_run = models[:]
    try:
        if run_models:
            while len(models_to_run) > 0:
                new_models_run = run_model(models_to_run[0], models_run,
                                           args.run_dependencies)
                for model in new_models_run:
                    models_to_run.remove(model)
                models_run.extend(new_models_run)
    except:
        cleanup(models, start)

    # Might need to reload models here to get the latest data
    if run_views:
        for view in views:
            try:
                log.info("Running view {}".format(view.__name__))
            except AttributeError:
                log.info("Running view {}".format(view.func.__name__))
            view()

    end = datetime.now()
    history = History(studies=studies, run_models=run_models,
                      run_views=run_views,
                      run_dependencies=args.run_dependencies,
                      start_time=start, end_time=end)
    settings.session.add(history)
    settings.session.commit()
