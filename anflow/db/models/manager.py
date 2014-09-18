from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import os
import inspect
import re
from functools import partial

from sqlalchemy import desc

from anflow.conf import settings
from anflow.db.data import DataSet
from anflow.db.history import History
from anflow.utils.debug import debug_message



class Manager(DataSet):

    def __init__(self, model_class):
        query = settings.session.query()
        super(Manager, self).__init__(query, model_class)
