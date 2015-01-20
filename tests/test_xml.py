import importlib
import os
import sys
import xml.etree.ElementTree as ET

import pytest

from anflow.simulation import Simulation
from anflow.xml import parameters_from_elem, parser_from_elem


@pytest.fixture
def testtree():

    path = os.path.join(os.path.dirname(__file__), "static/parameters.xml")
    return ET.parse(path)


@pytest.fixture
def sim(request):

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "static"))
    request.addfinalizer(lambda: sys.path.pop(0))
    return Simulation('blah')


class TestFunctions(object):

    def test_parameters_from_elem(self, testtree):
        """Test parameters_from_elem"""
        elem = testtree.find("./parser/parameters")
        parameters = parameters_from_elem(elem)
        assert parameters == [{'a': 96, 'b': 48, 'another_var': 0.1},
                              {'a': 96, 'b': 48, 'another_var': 0.4}]

    def test_parser_from_elem(self, testtree, sim):
        """Test parser_from_elem"""
        elem = testtree.find("./parser")
        mod = importlib.import_module('somemod')
        parser_from_elem(sim, elem, None)
        assert "parsed_data" in sim.parsers
        assert (sim.parsers['parsed_data'].path_template
                == "{a}_{b}_{another_var}_{foo}.txt")
        assert sim.parsers['parsed_data'].loader == mod.some_func
        assert sim.parsers['parsed_data'].auxparams == {'foo': ['text1',
                                                                'text2']}