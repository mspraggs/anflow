from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.core.management import Manager



class TestManager(object):
    
    def test_constructor(self, settings):
        manager = Manager([])
        assert len(manager.anflow_commands.items()) > 0
