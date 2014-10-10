from __future__ import absolute_import

import os

import pytest

from anflow.config import Config



@pytest.fixture
def settings(tmp_dir, request):

    class Obj(object):
        pass

    ret = {'FOO': 5, 'BAR': 'blah'}
    obj = Obj()
    for key, value in ret.items():
        setattr(obj, key, value)

    filename = os.path.join(tmp_dir, 'settings.py')
    with open(filename, 'w') as f:
        for key, value in ret.items():
            f.write('{} = {}\n'.format(key, value.__repr__()))

    os.environ['PROJECT_SETTINGS'] = filename

    request.addfinalizer(lambda: os.unlink(filename))

    return {'dict': ret, 'obj': obj, 'file': filename,
            'envvar': 'PROJECT_SETTINGS'}

class TestSimulation(object):

    def test_init(self):
        config = Config()
        attributes = []

        for attr in attributes:
            assert hasattr(config, attr)

    def test_from_object(self, settings):
        config = Config()
        config.from_object(settings['obj'])

        for key, value in settings['dict'].items():
            assert getattr(config, key) == value

    def test_from_dict(self, settings):
        config = Config()
        config.from_dict(settings['dict'])

        for key, value in settings['dict'].items():
            assert getattr(config, key) == value

    def test_from_pyfile(self, settings):
        config = Config()
        config.from_pyfile(settings['file'])

        for key, value in settings['dict'].items():
            assert getattr(config, key) == value
        
    def test_from_envvar(self, settings):
        config = Config()
        config.from_envvar(settings['envvar'])

        for key, value in settings['dict'].items():
            assert getattr(config, key) == value
