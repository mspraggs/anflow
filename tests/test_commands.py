from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil

import jinja2
import pytest

from anflow.commands import startproject, startstudy


@pytest.fixture
def cleanup_project(tmp_dir, request):

    request.addfinalizer(lambda: shutil.rmtree(os.path.join(tmp_dir, "new_project")))


@pytest.fixture
def new_project(tmp_dir, cleanup_project):

    template_args = {}

    src_dir = os.path.join(os.path.dirname(__file__),
                           '../anflow/templates/project')
    target_dir = os.path.join(tmp_dir, 'new_project')
    os.makedirs(target_dir)
    for fname in ['manage.py', 'settings.py']:
        with open(os.path.join(src_dir, fname)) as f:
            template = jinja2.Template(f.read())
        with open(os.path.join(target_dir, fname), 'w') as f:
            f.write(template.render(**template_args))


def test_startproject(tmp_dir, cleanup_project):
    """Test startproject command"""

    startproject.main(["new_project", tmp_dir])
    assert os.path.exists(os.path.join(tmp_dir, "new_project/manage.py"))
    assert os.path.exists(os.path.join(tmp_dir, "new_project/settings.py"))


def test_startstudy(tmp_dir, new_project):
    """Test startstudy command"""
    import __main__
    old_main_file = __main__.__file__
    __main__.__file__ = os.path.join(tmp_dir, 'new_project/manage.py')
    startstudy.main(['some_study'])
    __main__.__file__ = old_main_file
    assert os.path.exists(os.path.join(tmp_dir, 'new_project/some_study/__init__.py'))
    assert os.path.exists(os.path.join(tmp_dir, 'new_project/some_study/simulation.py'))