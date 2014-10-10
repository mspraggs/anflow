from __future__ import absolute_import

import os

import pytest

from anflow import Simulation



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
        assert sim.config.RESULTS_DIR == os.path.join(tmp_dir, "results")

    
