from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import argparse
import importlib
import sys

from anflow.management import get_project_path, load_project_config


def gather_simulations(studies):
    """Goes through study locations and loads simulations"""
    config = load_project_config()
    simulations = []
    sys.path.insert(0, get_project_path())
    for study in studies:
        module_name = (config.COMPONENT_TEMPLATE.format(study_name=study,
                                                        component='simulation')
                       .replace('/', '.'))
        module = importlib.import_module(module_name)
        simulations.append(module.sim)
    sys.path.pop(0)
    return simulations


def sort_simulations(simulations):
    """Sorts the supplied simulations based on their dependencies using
    insertion sort"""
    for i, simulation in enumerate(simulations):
        j = i
        while j > 0 and simulations[j - 1] not in simulations[j].dependencies:
            simulations[j - 1], simulations[j] = (simulations[j],
                                                  simulations[j - 1])
            j -= 1
    return simulations


def main(argv):
    """Main command"""

    config = load_project_config()
    parser = argparse.ArgumentParser(description="Run models and views")
    parser.add_argument('--force', action='store_true', default=False,
                        help='Force a run of models and/or views')
    parser.add_argument('--studies', action='store',
                        help='Studies from which to run measurements')
    parser.add_argument('--model', action='store', help='Model to run')
    parser.add_argument('--view', action='store', help='View to run')
    options = parser.parse_args(argv)

    if options.studies:
        studies = options.studies.split(',')
    else:
        studies = config.ACTIVE_STUDIES

    if options.model:
        study, model = options.model.split('.')
        simulation = gather_simulations([study])[0]
        simulation.config.from_object(config)
        [s.config.from_object(config) for s in simulation.dependencies]
        simulation.run_model(model, options.force)
    elif options.view:
        study, view = options.model.split('.')
        simulation = gather_simulations([study])[0]
        simulation.config.from_object(config)
        simulation.run_view(view, options.force)
    else:
        simulations = gather_simulations(studies)
        simulations = sort_simulations(simulations)
        for simulation in simulations:
            simulation.config.from_object(config)
            simulation.run(options.force)