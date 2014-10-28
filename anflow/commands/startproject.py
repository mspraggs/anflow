from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import shutil
from importlib import import_module

from jinja2 import Template

def main(argv):
    
    project_name = argv[0]
    try:
        location = argv[1]
    except IndexError:
        location = '.'
    template_args = {'project_name': project_name}
    # Check that the project doesn't already exist
    try:
        module = import_module(project_name)
    except ImportError as e:
        debug_message(e)
    else:
        # ERROR MESSAGE HERE
        return
    # Now iterate through the project template and substitute in the
    # template arguments to each file
    tree = os.walk(settings.PROJECT_TEMPLATE)
    for directory, subdirs, files in tree:
        relative_directory = os.path.relpath(directory,
                                             settings.PROJECT_TEMPLATE)

        new_directory = os.path.join(location, project_name, relative_directory)
        try:
            os.makedirs(new_directory)
            open(os.path.join(new_directory, "__init__.py"), 'a').close()
        except OSError as e:
            debug_message(e)

        for f in files:
            template_file_path = os.path.join(location, directory, f)
            new_file_path = os.path.join(new_directory, f)
            with open(template_file_path) as file_handle:
                template = Template(file_handle.read())
            with open(new_file_path, 'w') as file_handle:
                file_handle.write(template.render(**template_args))
