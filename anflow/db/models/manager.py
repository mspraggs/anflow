from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import inspect
import re
from functools import partial

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from anflow.conf import settings
from anflow.db.data import DataSet



Base = declarative_base()

class Manager(DataSet):

    def __init__(self, model_class):

        engine = create_engine(settings.DB_PATH)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()
        query = self.session.query()
        super(Manager, self).__init__(query, model_class)
