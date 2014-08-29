from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function



class DataSet(list):

    def __init__(self, *args):
        list.__init__(self, *args)

    def filter(self, **kwargs):
        pass
