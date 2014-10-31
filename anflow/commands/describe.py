from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from anflow.management import (gather_simulations, load_project_config,
                               sort_simulations)
from anflow.utils import extract_from_format


def main(argv):
    """Main function"""

    config = load_project_config()
    simulations = sort_simulations(gather_simulations(config.ACTIVE_STUDIES))

    print("Project models and views by study:")
    print()

    for simulation in simulations:
        match = extract_from_format(config.COMPONENT_TEMPLATE.replace('/', '.'),
                                    simulation.import_name)
        print("[{}.models]".format(match.group('study_name')))
        for model in simulation.models.keys():
            print("    {}.{}".format(match.group('study_name'), model))
        print("[{}.views]".format(match.group('study_name')))
        for view in simulation.views.keys():
            print("    {}.{}".format(match.group('study_name'), view))
        print()