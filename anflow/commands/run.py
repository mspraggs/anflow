from __future__ import absolute_import
from __future__ import unicode_literals

import xml.etree.ElementTree as ET
import sys

from anflow.management import load_project_config
from anflow.xml import simulation_from_etree


def main(argv):
    """Main command"""

    config = load_project_config()

    try:
        input_file = argv[0]
    except IndexError:
        print("Usage: {} run <input xml file>".format(sys.argv[0]))

    tree = ET.parse(input_file)
    simname = input_file.replace("/", "_").replace(".", "_")
    simulation, parameters, queries = simulation_from_etree(tree, simname)
    simulation.config.from_object(config)

    for tag in simulation.models.keys():
        simulation.run_model(tag,parameters[tag], queries[tag])

    for tag in simulation.views.keys():
        simulation.run_view(tag, parameters[tag], queries[tag])
