from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from jinja2 import Template

from anflow.management import get_project_path, load_project_config


def main(argv):
    # TODO: Significant revision of this function needed
    study_name = argv[0]
    template_args = {'study_name': study_name}

    template_path = os.path.join(os.path.dirname(__file__),
                                 '../templates/study')
    project_path = get_project_path()
    config = load_project_config()

    for filename in os.listdir(template_path):
        with open(os.path.join(template_path, filename)) as f:
            template = Template(f.read())
        study_filepath = os.path.join(
            project_path,
            config.COMPONENT_TEMPLATE.format(study_name=study_name,
                                             component=filename)
        )
        try:
            os.makedirs(os.path.dirname(study_filepath))
        except OSError:
            pass
        with open(study_filepath, 'w') as f:
            f.write(template.render(**template_args))

    for directory in [config.RESULTS_PATH, config.REPORTS_PATH]:
        try:
            os.makedirs(directory)
        except OSError as e:
            pass
