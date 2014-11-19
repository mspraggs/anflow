from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import sys

import pytest

from anflow.management import Manager, get_project_path, load_project_config


@pytest.fixture(scope="session")
def project_path(tmp_dir, request):
    import __main__
    old_main_file = __main__.__file__

    project_path = os.path.join(tmp_dir, 'temp_project')
    shutil.copytree(os.path.join(os.path.dirname(__file__),
                                 'static/dummy_project'),
                    project_path)
    for fname in ['manage.py', 'settings.py']:
        shutil.copy(os.path.join(os.path.dirname(__file__),
                                 '../anflow/templates/project',
                                 fname),
                    os.path.join(project_path, fname))
    __main__.__file__ = os.path.join(project_path, 'manage.py')

    def fin():
        shutil.rmtree(project_path, ignore_errors=True)
        __main__.__file__ = old_main_file

    request.addfinalizer(fin)
    return project_path


class TestFunctions(object):

    def test_get_project_path(self, project_path):
        """Test get_project_path"""
        assert get_project_path() == project_path

    def test_load_project_config(self):
        """Test load_project_config"""
        config = load_project_config()
        assert config.ACTIVE_STUDIES == []
        assert config.LOGGING_LEVEL == 20
        assert config.LOGGING_CONSOLE


class TestManager(object):

    def test_init(self):
        """Test for Manager constructor"""
        manager = Manager()
        assert manager.argv == sys.argv
        assert (manager.anflow_commands.keys()
                == ["startstudy", "describe", "run", "startproject"])
