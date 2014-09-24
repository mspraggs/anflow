from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import Column, String

from anflow.db.models import Model



class CachedData(Model):

    abstract = True
    label = Column(String(100))
    hash = Column(String(32))
