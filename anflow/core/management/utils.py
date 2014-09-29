from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import importlib

from anflow.conf import settings
from anflow.db.models import Model
from anflow.utils.debug import debug_message
from anflow.utils.logging import logger



def gather_models(studies):
    """Looks through the specified studies and gathers any models"""
    log = logger()
    models = []
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
    return models

def gather_views(studies):
    """Goes through the supplied studies and """
    log = logger()
    views = []
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
    return views
