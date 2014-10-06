from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
import os
import shutil
import sys

import pytest

from anflow.core.management import Manager



@pytest.fixture
def model_files_setup(settings):
    """Fixture for setting up model files - basically dump the MyModel source to
    the foo models file"""
    source_file = os.path.join(os.path.dirname(__file__),
                               "static/dummy_model.py")
    models_filename = os.path.join(settings.PROJECT_ROOT,
                                   settings.COMPONENT_TEMPLATE
                                   .format(study_name="foo",
                                           component="models.py"))
    init_filename = os.path.join(os.path.dirname(models_filename),
                                 "__init__.py")
    try:
        os.makedirs(os.path.dirname(models_filename))
        with open(init_filename, 'a') as f:
            pass
    except OSError:
        pass
    shutil.copyfile(source_file, models_filename)

    models_filename = os.path.join(settings.PROJECT_ROOT,
                                   settings.COMPONENT_TEMPLATE
                                   .format(study_name="bar",
                                           component="models.py"))
    init_filename = os.path.join(os.path.dirname(models_filename),
                                 "__init__.py")
    try:
        os.makedirs(os.path.dirname(models_filename))
        with open(init_filename, 'a') as f:
            pass
    except OSError:
        pass
    with open(models_filename, 'w') as f:
        pass

class TestManager(object):

    def test_constructor(self, settings):
        manager = Manager([])
        assert len(manager.anflow_commands.items()) > 0

class TestStartProject(object):

    def test_main(self, base_settings):

        from anflow.core.management.commands import startproject
        startproject.main(["new_project", base_settings.tmp_dir])

        tree = os.walk(base_settings.PROJECT_TEMPLATE)
        for dirpath, dirnames, filenames in tree:
            for filename in filenames:
                if filename.endswith(".py"):
                    assert os.path.exists(os.path.join(base_settings.tmp_dir,
                                                       dirpath, filename))

class TestStartStudy(object):

    def test_main(self, settings):

        from anflow.core.management.commands import startstudy
        study_name = "new_study"
        startstudy.main([study_name])

        for component in ["models", "views"]:
            path = os.path.join(settings.PROJECT_ROOT,
                                settings.COMPONENT_TEMPLATE
                                .format(study_name=study_name,
                                        component=(component + ".py")))
            assert os.path.exists(path)

        for template in [settings.RAWDATA_TEMPLATE, settings.REPORTS_TEMPLATE]:
            template = os.path.join(settings.PROJECT_ROOT, template)
            assert os.path.exists(template.format(study_name=study_name))

class TestSyncDB(object):

    def test_main(self, model_files_setup):
        from anflow.core.management.commands import syncdb
        syncdb.main([])

        # Try to import and use the new model
        from foo.models import MyModel
        MyModel.data.all()
