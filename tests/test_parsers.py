from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.core.data import DataSet, Datum
from anflow.core.parsers.base import BaseParser
from anflow.core.parsers import BlindParser, GuidedParser

import importlib
import inspect
from itertools import product
import os
import shutil

import pytest
import numpy as np

from anflow.utils.io import projectify



@pytest.fixture()
def study_base_parser(settings, request):
    component_file = projectify(settings.COMPONENT_TEMPLATE
                                .format(component='models', study_name='foo')
                                + ".py")
    component_directory = os.path.dirname(component_file)
    os.makedirs(component_directory)
    loader_path = os.path.join(os.path.dirname(__file__),
                               "static/parser_loaders.py")
    shutil.copyfile(loader_path, component_file)
        
    for dirpath, dirnames, filenames in os.walk(settings.PROJECT_ROOT):
        open(os.path.join(dirpath, '__init__.py'), 'w').close()

    module_name = os.path.relpath(component_file)[:-3].replace('/', '.')
    module = importlib.import_module(module_name, 'test_project')

    return module.get_base_parser()

@pytest.fixture()
def study_blind_parser(settings, request):
    component_file = projectify(settings.COMPONENT_TEMPLATE
                                .format(component='models', study_name='foo')
                                + ".py")
    component_directory = os.path.dirname(component_file)
    os.makedirs(component_directory)
    loader_path = os.path.join(os.path.dirname(__file__),
                               "static/parser_loaders.py")
    shutil.copyfile(loader_path, component_file)
        
    for dirpath, dirnames, filenames in os.walk(settings.PROJECT_ROOT):
        open(os.path.join(dirpath, '__init__.py'), 'w').close()

    for mass, config in product(np.arange(0.1, 0.8, 0.1), range(100)):
        filename = projectify(os.path.join(settings.RAWDATA_TEMPLATE,
                                           'data_m{}.{}.pkl'
                                           .format(mass, config)))
        datum = Datum({}, np.arange(10), filename)
        datum.save()

    module_name = os.path.relpath(component_file)[:-3].replace('/', '.')
    module = importlib.import_module(module_name, 'test_project')

    return module.get_blind_parser()

class TestBaseParser(object):

    def test_constructor(self, settings, study_base_parser):

        assert study_base_parser.study == 'foo'
        assert study_base_parser.rawdata_dir.endswith(settings.RAWDATA_TEMPLATE
                                                      .format(study_name='foo'))
        assert isinstance(study_base_parser.parsed_data, DataSet)
        assert study_base_parser.populated == False

    def test_set_path_format(self, settings, study_base_parser):

        params = {'ok': 1, 'computer': 0.5}
        study_base_parser.parsed_data.append(Datum(params, [0, 1, 2], 'spam'))
        study_base_parser.set_path_format()
        assert study_base_parser.path_format == 'computer{computer}_ok{ok}.pkl'

    def test_iterator(self, study_base_parser):

        sample_datum = Datum({'a': 1}, [1, 2, 3], 'some_file')
        for i in range(10):
            study_base_parser.parsed_data.append(sample_datum)

        datum_dump = []
        for datum in study_base_parser:
            datum_dump.append(datum)
            assert datum == sample_datum

        assert len(datum_dump) == 10

class TestBlindParser(object):

    def test_populate(self, study_blind_parser):

        study_blind_parser.populate()
        assert study_blind_parser.populated
        assert len(study_blind_parser.parsed_data) == 700
