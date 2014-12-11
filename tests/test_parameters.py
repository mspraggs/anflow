from __future__ import absolute_import
from __future__ import unicode_literals

from anflow.parameters import global_sweep, hub_and_spokes


class TestFunctions(object):

    def test_global_sweep(self):
        """Test the global sweep parameter set generation function"""
        parameters = global_sweep(a=range(5), b=range(10), c=["tree", "car"])
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