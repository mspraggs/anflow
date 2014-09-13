from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import (Boolean, Column, DateTime, Integer, PickleType)
from sqlalchemy.ext.declarative import declarative_base

from anflow.db.models.base import Base



class History(Base):

    __tablename__ = "project_history"

    id = Column(Integer, primary_key=True)
    studies = Column(PickleType)
    run_models = Column(Boolean)
    run_views = Column(Boolean)
    run_dependencies = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
