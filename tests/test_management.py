from __future__ import absolute_import
from __future__ import unicode_literals

from anflow.management import Manager



class TestManager(object):

    def test_constructor(self):
        """Test for Manager constructor"""
        manager = Manager()
        assert manager.argv == []
