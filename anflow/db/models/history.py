from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import Boolean, Column, DateTime, PickleType, String
from sqlalchemy.orm import relationship

from anflow.db.models.base import BaseModel



class History(BaseModel):

    __tablename__ = "project_history"

    studies = Column(PickleType)
    run_models = Column(Boolean)
    run_views = Column(Boolean)
    run_dependencies = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    comment = Column(String(200))
