from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import inspect
import os
import sys



def execute_from_command_line(argv=None):
    manager = Manager(argv)
    manager.execute()

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
        self.argv = argv or []

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

