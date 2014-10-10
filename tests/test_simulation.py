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

        assert sim.models == {'some_func': (some_func, input_data, None)}
        assert hasattr(some_func, 'results')
        assert len(some_func.results) == 0
        assert some_func.results._parent == some_func

    def test_run_model(self, sim, tmp_dir):
        """Test Simulation.run_model"""

        params = {'a': 1}
        datum = Datum(params, 1.0)
        datum.save()
        input_data = [datum]
        @sim.register_model(input_data=input_data)
        def some_func(data):
            return data
        @sim.register_model(input_data=some_func.results)
        def another_func(data):
            return data

        sim.run_model('some_func')
        assert os.path.exists(os.path.join(tmp_dir, "results",
                                           'some_func_a1.pkl'))
        sim.run_model('another_func')
        assert os.path.exists(os.path.join(tmp_dir, "results",
                                           'another_func_a1.pkl'))
