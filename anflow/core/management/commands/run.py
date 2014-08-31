from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from itertools import product
from importlib import import_module

from anflow.core.models import Model
from anflow.utils.debug import debug_message

import settings

def run_model(model_class):

    model = model_class()
    models_run = []
    if model.depends_on:
        for dependency in model.depends_on:
            models_run.extend(run_model(model_class))

    if model.parameters:
        for params in model.parameters:
            try:
                model.run(*params[0], **params[1])
            except (IndexError, TypeError) as e:
                debug_message(e)
            try:
                model.run(**params)
            except TypeError as e:
                debug_message(e)
                model.run(*params)
    else:
        model.run()
    model.save()
    models_run.append(model_class)
    return models_run

def main(argv):

    models = []
    views = []
    for study in settings.ACTIVE_STUDIES:
        module = import_module(settings.COMPONENT_TEMPLATE
                               .format(component='models',
                                       study_name=study)
                               .replace('/', '.'))
        for name in dir(module):
            member = getattr(module, name)
            try:
                if issubclass(member, Model):
                    models.append(member)
            except TypeError as e:
                debug_message(e)
                
    for study in settings.ACTIVE_STUDIES:
        module = import_module(settings.COMPONENT_TEMPLATE
                               .format(component='views',
                                       study_name=study)
                               .replace('/', '.'))
        views.extend(module.view_functions)

    while len(models) > 0:
        models_run = run_model(models[0])
        for model in models_run:
            models.remove(model)

    for view in views:
        view()
