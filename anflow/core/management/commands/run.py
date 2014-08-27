from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from itertools import product
from importlib import import_module

from anflow.core.models import Model
from anflow.utils.debug import debug_message

import settings

def main(argv):

    components = ['models', 'views']
    
    for component, study in product(components, settings.ACTIVE_STUDIES):
        module = import_module(settings.COMPONENT_TEMPLATE
                               .format(component=component,
                                       study_name=study)
                               .replace('/', '.'))
        models = []
        for name in dir(module):
            member = getattr(module, name)
            try:
                if issubclass(member, Model):
                    models.append(member)
            except TypeError as e:
                debug_message(e)

        for model in models:
            themodel = model()
            if themodel.parameters:
                for params in themodel.parameters:
                    try:
                        themodel.run(*params[0], **params[1])
                    except (IndexError, TypeError) as e:
                        debug_message(e)
                        try:
                            themodel.run(**params)
                        except TypeError as e:
                            debug_message(e)
                            themodel.run(*params)
            else:
                themodel.run()
            themodel.save()
                
