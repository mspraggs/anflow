from __future__ import absolute_import
from __future__ import unicode_literals

import sys

from anflow.management import Manager



class TestManager(object):

    def test_init(self):
        """Test for Manager constructor"""
        manager = Manager()
        assert manager.argv == sys.argv
        assert (manager.anflow_commands.keys()
                == ["startstudy", "run", "startproject"])
