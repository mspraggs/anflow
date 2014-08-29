from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import sys
import os
import inspect
import importlib

from anflow.conf import ENVIRONMENT_VARIABLE, settings
from anflow.utils.debug import debug_message

def execute_from_command_line(argv=None):
    manager = Manager(argv)
    manager.execute()

class Manager(object):
    
    def __init__(self, argv):
        self.anflow_commands = {}

        # debug_message relies on the DEBUG setting, so we need to set up the
        # settings before we do anything else
        if not os.environ.get(ENVIRONMENT_VARIABLE):                
            os.environ[ENVIRONMENT_VARIABLE] = "anflow.conf.global_settings"
        # Now configure the settings
        settings.configure()
        
        # Look for commands in the commands sub-directory
        commands_dir = os.path.join(os.path.dirname(__file__), "commands")
        files = os.listdir(commands_dir)
        this_module_name = inspect.getmodule(self).__name__
        for f in files:
            module_name = "{}".format(inspect.getmodulename(f))
            # Try to locate a main() function in the current file
            try:
                module = importlib.import_module(".commands.{}"
                                                 .format(module_name),
                                                 this_module_name)
                function = module.main
                self.anflow_commands[module_name] = function
            except (ImportError, AttributeError) as e:
                debug_message(e, module_name)
            
        # Get any available arguments
        self.argv = argv or sys.argv

    def execute(self):
        try:
            self.anflow_commands[self.argv[1]](self.argv[2:])
        except (IndexError, KeyError) as e:
            debug_message(e)
            self.help()

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
