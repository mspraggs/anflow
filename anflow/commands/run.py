from __future__ import absolute_import
from __future__ import unicode_literals

import argparse

from anflow.commands import describe
from anflow.management import (gather_simulations, load_project_config,
                               sort_simulations)


def main(argv):
    """Main command"""

    config = load_project_config()
    parser = argparse.ArgumentParser(description="Run models and views")
    parser.add_argument('--force', action='store_true', default=False,
                        help='Force a run of models and/or views')
    parser.add_argument('--dry-run', action='store_true', default=False,
                        help='Don\'t save the results from a model')
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
        try:
            study, model = options.model.split('.')
        except ValueError:
            # Model specification format (study.model) not followed
            print("Model specification error. Format: <study>.<model>")
            describe.main(argv)
            return
        try:
            simulation = gather_simulations([study])[0]
        except ImportError:
            # Cannot find the study in the project tree
            print("Study specification error.")
            describe.main(argv)
            return
        if model not in simulation.models.keys():
            # Model doesn't exist
            print("Cannot find model {} in study {}".format(study, study))
            describe.main(argv)
            return

        simulation.config.from_object(config)
        [s.config.from_object(config) for s in simulation.dependencies]
        simulation.run_model(model, options.force, options.dry_run)
    elif options.view:
        try:
            study, view = options.view.split('.')
        except ValueError:
            # View specification format (study.view) not followed
            print("View specification error. Format: <study>.<view>")
            describe.main(argv)
            return
        try:
            simulation = gather_simulations([study])[0]
        except ImportError:
            # Cannot find the study in the project tree
            print("Study specification error.")
            describe.main(argv)
            return
        if view not in simulation.views.keys():
            from .describe import main
            main(argv)
            return

        simulation.config.from_object(config)
        [s.config.from_object(config) for s in simulation.dependencies]
        simulation.run_view(view, options.force)
    else:
        simulations = gather_simulations(studies)
        simulations = sort_simulations(simulations)
        for simulation in simulations:
            simulation.config.from_object(config)
            simulation.run(options.force, options.dry_run)
