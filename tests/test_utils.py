from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import os
import sys

import pytest

from anflow.utils import get_dependency_files, get_root_path



@pytest.fixture
def dummy_module(tmp_dir, request):

    sys.path.insert(0, tmp_dir)

    with open(os.path.join(tmp_dir, "__init__.py"), 'w') as f:
        pass
    with open(os.path.join(tmp_dir, "somemod.py"), 'w') as f:
        f.write('import sys\n')
        f.write('from anothermod import some_func\n')
    with open(os.path.join(tmp_dir, 'anothermod.py'), 'w') as f:
        f.write('import os\n')
        f.write('def some_func(): pass\n')

    def fin():
        for filename in ['__init__.py', 'anothermod.py', 'somemod.py']:
            try:
                os.unlink(os.path.join(tmp_dir, filename))
            except OSError:
                pass
        sys.path.remove(tmp_dir)
    request.addfinalizer(fin)

    return ['somemod', 'anothermod']

class TestFunctions(object):

    def test_get_root_path(self, tmp_dir, dummy_module):
        """Test get_root_path function"""
        # First try a module that doesn't exist
        assert get_root_path('blah') == os.getcwd()
        # Then try __main__
        assert get_root_path('__main__') == os.path.dirname(sys.executable)
        # Then the dummy_module
        assert get_root_path(dummy_module[0]) == tmp_dir

    def test_get_dependency_files(self, dummy_module, tmp_dir):
        """Test get_dependency_files"""

        mod = importlib.import_module(dummy_module[0])
        files = get_dependency_files(mod, tmp_dir)

        assert files == [os.path.join(tmp_dir, 'anothermod.py'),
                         os.path.join(tmp_dir, 'somemod.py')]
