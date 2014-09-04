from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import inspect
import os
import re

from anflow.conf import settings

def reports_path(filename):
    study = None
    component_regex = re.compile(re.sub(r'\{ *(?P<var>\w+) *\}',
                                        '(?P<\g<var>>.+)',
                                        settings.COMPONENT_TEMPLATE))
    stack = inspect.stack()
    for frame in stack:
        # THIS METHOD IS NOT INDEPENDENT OF THE PROJECT LAYOUT
        relative_path = os.path.relpath(frame[1], settings.PROJECT_ROOT)
        result = component_regex.search(relative_path)
        if result:
            study = result.group('study_name')
        if study in settings.ACTIVE_STUDIES:
            break
    
    return os.path.join(settings.REPORTS_TEMPLATE.format(study_name=study),
                        filename)

def projectify(path):
    """Prepends path with the project root"""
    return os.path.join(settings.PROJECT_ROOT, path)
