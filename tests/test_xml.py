import importlib
import os
import sys
import xml.etree.ElementTree as ET

import pytest

from anflow.simulation import Simulation
from anflow.xml import (input_from_elem, parameters_from_elem, parser_from_elem,
                        query_from_elem)


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

    def check_model_query(self, query):
        """Evaluate supplied query on sample parameter set to check behaviour"""
        sample_params = [{'a': a, 'b': b}
                         for a in range(94, 100)
                         for b in range(10)]
        filtered_params = [{'a': 96, 'b': b} for b in range(10)]
        assert len(query.evaluate(sample_params)) == 10
        assert query.evaluate(sample_params) == filtered_params

    def test_parameters_from_elem(self, testtree):
        """Test parameters_from_elem"""
        elem = testtree.find("./parser/parameters")
        parameters = parameters_from_elem(elem)
        assert parameters == [{'a': 96, 'b': 48, 'another_var': 0.1},
                              {'a': 96, 'b': 48, 'another_var': 0.4}]

    def test_query_from_elem(self, testtree):
        """Test query_from_elem"""
        elem = testtree.find("./model/input/filter")
        query = query_from_elem(elem)
        self.check_model_query(query)

    def test_input_from_elem(self, testtree):
        """Test input_from_elem"""
        elem = testtree.find("./model/input")
        tag, query = input_from_elem(elem)
        assert tag == "parsed_data"
        self.check_model_query(query)

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

    def test_model_from_elem(self, testtree, sim):
        """Test model_from_elem"""
        elem = testtree.find("./model")
        mod = importlib.import_module('somemod')
        params, query = model_from_elem(sim, elem)
        self.check_model_query(query)
        assert params == [{'bar': 5.3, 'baz': 'yes'}, {'bar': 5.3, 'baz': 'no'}]
        assert 'model_some_func' in sim.models
        assert sim.models['model_some_func'].func == mod.some_func
        assert sim.models['model_some_func'].input_tag == 'parsed_data'
        assert sim.models['model_some_func'].path_template is None
