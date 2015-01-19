import os
import xml.etree.ElementTree as ET

import pytest

from anflow.xml import parameters_from_elem


@pytest.fixture
def testtree():

    path = os.path.join(os.path.dirname(__file__), "static/parameters.xml")
    return ET.parse(path)


class TestFunctions(object):

    def test_parameters_from_elem(self, testtree):
        """Test parameters_from_elem"""
        elem = testtree.find("./input/parameters")
        parameters = parameters_from_elem(elem)
        assert parameters == [{'a': 96, 'b': 48, 'another_var': 0.1},
                              {'a': 96, 'b': 48, 'another_var': 0.4}]
