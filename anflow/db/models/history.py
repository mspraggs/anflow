from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime

from sqlalchemy import Boolean, Column, DateTime, PickleType, String
from sqlalchemy.orm import relationship

from anflow.db.models.base import BaseModel



class History(BaseModel):

    studies = Column(PickleType)
    run_models = Column(Boolean)
    run_views = Column(Boolean)
    run_dependencies = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    comment = Column(String(200))
    models = relationship("Model", foreign_keys="Model.history_id",
                          backref="history")

    def __init__(self, *args, **kwargs):
        self.start_time = datetime.datetime.now()
        super(BaseModel, self).__init__(*args, **kwargs)

    def save(self):
        # N.B.: We can't put this default setting in the call to Column, because
        # that uses the server time, and since History.start_time and
        # Model.timestamp use the client time, this could cause issues.
        self.end_time = self.end_time or datetime.datetime.now()
        BaseModel.save(self)
