from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from argparse import ArgumentParser
from itertools import product
from importlib import import_module
import sys

from anflow.conf import settings
from anflow.core.models import Model
from anflow.utils.debug import debug_message

def run_model(model_class, run_dependencies=True):
    """Recursively run a model and its dependencies, returning a list of the
    models run"""
    models_run = []
    if model_class.depends_on and run_dependencies:
        for dependency in model_class.depends_on:
            models_run.extend(run_model(dependency, run_dependencies))
        
    model = model_class()
    try:
        if not model.input_stream.populated:
            model.input_stream.populate()
    except AttributeError as e:
        debug_message(e)
    if model.parameters:
        for params in model.parameters:
            try:
                model.run(*params[0], **params[1])
            except (IndexError, KeyError, TypeError) as e:
                debug_message(e)
            try:
                model.run(**params)
            except TypeError as e:
                debug_message(e)
                model.run(*params)
    else:
        model.run()
    model.save()

    del sys.modules[model_class.__module__]
    module = import_module(model_class.__module__)
    reload(module)
    
    models_run.append(model_class)
    return models_run

def main(argv):

    # TODO: Some arguments here to filter models, studies,
    # override running of dependencies, etc.

    parser = ArgumentParser()
    parser.add_argument('--study', dest='study', action='store',
                        default=None)
    parser.add_argument('--component', dest='component', action='store',
                        default=None)
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
    for study in studies:
        module = import_module(settings.COMPONENT_TEMPLATE
                               .format(component='models',
                                       study_name=study)
                               .replace('/', '.'))
        for name in dir(module):
            member = getattr(module, name)
            try:
                if issubclass(member, Model):
                    if not member.virtual:
                        models.append(member)
            except TypeError as e:
                debug_message(e)
                
    for study in settings.ACTIVE_STUDIES:
        module = import_module(settings.COMPONENT_TEMPLATE
                               .format(component='views',
                                       study_name=study)
                               .replace('/', '.'))
        views.extend(module.view_functions)

    if run_models:
        while len(models) > 0:
            models_run = run_model(models[0])
            for model in models_run:
                models.remove(model)

    # Might need to reload models here to get the latest data
    if run_views:
        for view in views:
            view()
