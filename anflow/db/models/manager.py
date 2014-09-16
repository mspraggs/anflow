from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import os
import inspect
import re
from functools import partial

from sqlalchemy import create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from anflow.conf import settings
from anflow.db.data import DataSet
from anflow.db.history import History
from anflow.utils.debug import debug_message



Base = declarative_base()

class Manager(DataSet):

    def __init__(self, model_class):

        engine = create_engine(settings.DB_PATH)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        self.session = DBSession()
        query = self.session.query()
        super(Manager, self).__init__(query, model_class)

    def latest(self):

        history = self.session.query(History).order_by(desc(History.end_time))
        history = history.__iter__()
        results = []

        while not results:
            try:
                run = history.next()
            except StopIteration as e:
                debug_message(e)
                new_query = self.query
                break
            new_query = self.query.filter(self.model_class.timestamp
                                          > run.end_time)
            results = new_query.all()

        return DataSet(new_query, self.model_class)
