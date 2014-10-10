from __future__ import absolute_import

import os

import pytest

from anflow import Simulation
from anflow.data import Datum



@pytest.fixture
def sim(tmp_dir):

    settings = {}
    settings['RESULTS_DIR'] = os.path.join(tmp_dir, "results")

    sim = Simulation()
    sim.config.from_dict(settings)
    return sim

class TestSimulation(object):

    def test_init(self, sim, tmp_dir):
        """Test object constructor"""
        assert hasattr(sim, 'config')
        assert sim.config.RESULTS_DIR == os.path.join(tmp_dir,
                                                      "results")

    def test_register_model(self, sim):
        """Test Simulation.register_model"""

        params = {'a': 1}
        input_data = [Datum(params, 1.0)]
        @sim.register_model(input_data=input_data)
        def some_func(data):
            pass

        assert sim.models == {'some_func': (some_func, input_data, params)}
