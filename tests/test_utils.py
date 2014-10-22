from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import os
import sys

import pytest

from anflow.utils import get_root_path



@pytest.fixture
def dummy_module(tmp_dir, request):

    sys.path.insert(0, tmp_dir)

    with open(os.path.join(tmp_dir, "__init__.py"), 'a') as f:
        pass
    with open(os.path.join(tmp_dir, "somemod.py"), 'a') as f:
        pass

    def fin():
        try:
            os.unlink(os.path.join(tmp_dir, '__init__.py'))
        except OSError:
            pass
        try:
            os.unlink(os.path.join(tmp_dir, 'somemod.py'))
        except OSError:
            pass
        sys.path.remove(tmp_dir)
    request.addfinalizer(fin)

    return 'somemod'

class TestFunctions(object):

    def test_get_root_path(self, tmp_dir, dummy_module):
        """Test get_root_path function"""
        # First try a module that doesn't exist
        assert get_root_path('blah') == os.getcwd()
        # Then try __main__
        assert get_root_path('__main__') == os.path.dirname(sys.executable)
        # Then the dummy_module
        assert get_root_path(dummy_module) == tmp_dir
