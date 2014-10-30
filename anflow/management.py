from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import importlib
import inspect
import os
import sys

from anflow.config import Config, project_defaults


def execute_from_command_line(argv=None):
    manager = Manager(argv)
    manager.execute()


def get_project_path():
    """Retrieves the project path by looking up the stack"""
    import __main__
    if __main__.__file__.endswith('manage.py'):
        return os.path.join(os.path.dirname(__main__.__file__))
    else:
        raise RuntimeError("Trying to work with project without using manage.py")

def load_project_config():
    """Loads the project settings found in settings.py and returns a Config
    object"""
    project_path = get_project_path()
    settings_file = os.path.join(project_path, "settings.py")
    config = Config()
    config.from_dict(project_defaults)
    config.from_pyfile(settings_file)
    return config


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


class Manager(object):

    def __init__(self, argv=None):
        self.anflow_commands = {}

        # Look for commands in the commands sub-directory
        commands_dir = os.path.join(os.path.dirname(__file__), "commands")
        files = os.listdir(commands_dir)
        for f in files:
            module_name = "{}".format(inspect.getmodulename(f))
            # Try to locate a main() function in the current file
            try:
                module = importlib.import_module("anflow.commands.{}"
                                                 .format(module_name))
                function = module.main
                self.anflow_commands[module_name] = function
            except (ImportError, AttributeError) as e:
                pass

        # Get any available arguments
        self.argv = argv or sys.argv

    def execute(self):
        try:
            command = self.anflow_commands[self.argv[1]]
        except (IndexError, KeyError) as e:
            self.help()
        else:
            command(self.argv[2:])

    def help(self):
        print("Usage: {} subcommand [options] [args]"
              .format(os.path.basename(self.argv[0])))
        print("Available subcommands:")
        print()
        print("[anflow]")
        commands = self.anflow_commands.keys()
        commands.sort()
        for command in commands:
            print("    {}".format(command))