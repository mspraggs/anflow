from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.conf import settings
from anflow.db.query.dataset import DataSet



class Manager(DataSet):

    def __init__(self, model_class):
        query = settings.session.query()
        super(Manager, self).__init__(query, model_class)
