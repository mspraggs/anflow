from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os

from jinja2 import Template

from anflow.conf import settings
from anflow.utils.debug import debug_message

def main(argv):
    study_name = argv[0]
    template_args = {'study_name': study_name}

    file_template = settings.COMPONENT_TEMPLATE
    
    paths = {}
    for component in settings.STUDY_COMPONENTS:
        new_path = (settings.COMPONENT_TEMPLATE
                    .format(study_name=study_name,
                            component=(component + ".py")))
        if os.path.exists(new_path):
            return
        paths[component] = new_path

    for component, path in paths.items():
        try:
            os.makedirs(os.path.dirname(path))
            open(os.path.join(os.path.dirname(path),
                              "__init__.py"), 'a').close()
        except OSError as e:
            debug_message(e, path)

        template_file = os.path.join(settings.STUDY_TEMPLATE, component + ".py")
        with open(template_file) as f:
            template = Template(f.read())
        with open(path, 'w') as f:
            f.write(template.render(**template_args))

    for template in [settings.RAWDATA_TEMPLATE,
                     settings.RESULTS_TEMPLATE,
                     settings.REPORTS_TEMPLATE]:
        try:
            os.makedirs(template.format(study_name=study_name))
        except OSError as e:
            debug_message(e)
