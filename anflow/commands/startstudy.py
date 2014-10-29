from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from jinja2 import Template

from anflow.management import get_project_path, load_project_config


def main(argv):
    study_name = argv[0]
    template_args = {'study_name': study_name}

    template_path = os.path.join(os.path.dirname(__file__),
                                 '../templates/study')
    project_path = get_project_path()
    config = load_project_config()
    
    paths = {}
    for component in config.STUDY_COMPONENTS:
        new_path = (config.COMPONENT_TEMPLATE
                    .format(study_name=study_name,
                            component=(component + ".py")))
        new_path = os.path.join(project_path, new_path)
        if os.path.exists(new_path):
            return
        paths[component] = new_path

    for component, path in paths.items():
        try:
            os.makedirs(os.path.dirname(path))
            open(os.path.join(os.path.dirname(path),
                              "__init__.py"), 'a').close()
        except OSError:
            pass

        template_file = os.path.join(template, component + ".py")
        with open(template_file) as f:
            template = Template(f.read())
        with open(path, 'w') as f:
            f.write(template.render(**template_args))

    for template in [config.RAWDATA_TEMPLATE,
                     config.REPORTS_TEMPLATE]:
        template = os.path.join(project_path, template)
        try:
            os.makedirs(template.format(study_name=study_name))
        except OSError as e:
            pass
