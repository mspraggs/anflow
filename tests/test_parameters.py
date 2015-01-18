from __future__ import absolute_import
from __future__ import unicode_literals

import xml.etree.ElementTree as ET

import pytest

from anflow.parameters import (generate_etree, add_sweep, hub_and_spokes,
                               parse_etree)


@pytest.fixture
def xml_params():

    root = ET.Element('root')

    for a, b in [(x, y) for x in range(10) for y in range(10)]:
        parameter_set = ET.SubElement(root, "parameters")
        elem_a = ET.SubElement(parameter_set, "a")
        elem_a.text = str(a)
        elem_b = ET.SubElement(parameter_set, 'b')
        elem_b.text = str(b)

    return root

class TestFunctions(object):

    def test_global_sweep(self):
        """Test the global sweep parameter set generation function"""
        parameters = add_sweep([{}], a=range(5), b=range(10), c=["tree", "car"])
        assert len(parameters) == 100
        for params in [dict(a=a, b=b, c=c) for a in range(5) for b in range(10)
                       for c in ["tree", "car"]]:
            assert params in parameters

    def test_hub_and_spokes(self):
        """Test the hub and spokes parameter set generation function"""
        parameters = hub_and_spokes({'a': 1, 'b': 2, 'c': 'foo'},
                                    a=range(2, 10), b=range(3, 5),
                                    c=['tree', 'bush'])
        assert len(parameters) == 13
        assert {'a': 1, 'b': 2, 'c': 'foo'} in parameters
        for a in range(2, 10):
            assert {'a': a, 'b': 2, 'c': 'foo'} in parameters
        for b in range(3, 5):
            assert {'a': 1, 'b': b, 'c': 'foo'} in parameters
        for c in ['tree', 'bush']:
            assert {'a': 1, 'b': 2, 'c': c} in parameters

    def test_parse_etree(self, xml_params):
        """Test xml parsing of parameters"""

        parameters = parse_etree(xml_params, '/')
        expected_params = [{'a': a, 'b': b}
                           for a in range(5) for b in range(10)]

        for params, expect_params in zip(parameters, expected_params):
            assert params == expect_params

    def test_generate_etree(self, xml_params):
        """Test xml generation of parameter lists"""

        params = [{'a': a, 'b': b} for a in range(10) for b in range(10)]
        etree = generate_etree(params, 'root')
        assert len(etree.getchildren()) == len(xml_params.getchildren())
        assert ET.tostring(etree) == ET.tostring(xml_params)