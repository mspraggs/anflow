from __future__ import absolute_import

import IPython

from anflow.management import (gather_simulations, load_project_config,
                               sort_simulations)


def main(argv):
    """Main command"""
    config = load_project_config()

    simulations = gather_simulations(config.ACTIVE_STUDIES)
    simulations = sort_simulations(simulations)
    for simulation in simulations:
        simulation.config.from_object(config)

    IPython.embed()