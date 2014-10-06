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
from anflow.core.management.utils import gather_models

def main(argv):

    models = gather_models(settings.ACTIVE_STUDIES)
    Base.metadata.create_all(settings.engine)
