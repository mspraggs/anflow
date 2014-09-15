from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import importlib

from sqlalchemy import create_engine

from anflow.conf import settings
from anflow.db import Base
from anflow.db.models import Model
from anflow.db.history import History
from anflow.db.models.cache import CachedData
from anflow.utils.debug import debug_message

def main(argv):

    engine = create_engine(settings.DB_PATH)

    models = []
    for study in settings.ACTIVE_STUDIES:
        module_name = (settings.COMPONENT_TEMPLATE
                       .format(component='models', study_name=study)
                       .replace('/', '.'))
        module = importlib.import_module(module_name)
        for name in dir(module):
            member = getattr(module, name)
            try:
                if issubclass(member, Model):
                    if member.__module__ == module_name:
                        models.append(member)
            except TypeError as e:
                debug_message(e)

    Base.metadata.create_all(engine)
