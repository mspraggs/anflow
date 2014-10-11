from __future__ import absolute_import

import os

import pytest

from anflow import Simulation
from anflow.data import Datum



@pytest.fixture
def sim(tmp_dir):

    settings = {}
    settings['RESULTS_DIR'] = os.path.join(tmp_dir, "results")
    
    params = {'a': 1}
    datum = Datum(params, 1.0, tmp_dir + '/')
    datum.save()
    input_data = [datum]

    sim = Simulation()
    sim.config.from_dict(settings)
    return {'simulation': sim, 'input_data': input_data}

class TestSimulation(object):

    def test_init(self, sim, tmp_dir):
        """Test object constructor"""
        assert hasattr(sim['simulation'], 'config')
        assert sim['simulation'].config.RESULTS_DIR == os.path.join(tmp_dir,
                                                                    "results")

    def test_register_model(self, sim):
        """Test Simulation.register_model"""

        simulation = sim['simulation']
        @simulation.register_model(input_data=sim['input_data'])
        def some_func(data):
            pass

        assert (simulation.models
                == {'some_func': (some_func, sim['input_data'], None)})
        assert hasattr(some_func, 'results')
        assert len(some_func.results._params) == 1
        assert some_func.results._parent == some_func

    def test_run_model(self, sim, tmp_dir):
        """Test Simulation.run_model"""
        
        simulation = sim['simulation']
        @simulation.register_model(input_data=sim['input_data'])
        def some_func(data):
            return data
        @simulation.register_model(input_data=some_func.results)
        def another_func(data):
            return data

        simulation.run_model('some_func')
        assert os.path.exists(os.path.join(tmp_dir, "results",
                                           'some_func_a1.pkl'))
        simulation.run_model('another_func')
        assert os.path.exists(os.path.join(tmp_dir, "results",
                                           'another_func_a1.pkl'))
