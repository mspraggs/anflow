from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import re

from anflow.conf import settings

def get_study(module_string):
    """Retrieves the study the supplied object belongs to"""
    module_component = settings.COMPONENT_TEMPLATE.replace('/', '.')
    component_regex = re.sub(r'\{ *(?P<var>\w+) *\}', '(?P<\g<var>>\w+)',
                             module_component)
    result = re.search(component_regex, module_string)
    if result:
        return result.group('study_name')
    else:
        return
