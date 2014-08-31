from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.conf import settings

def reports_path(filename):

    stack = inspect.stack()
    for frame in stack:
        relative_path = os.path.relpath(frame[1], settings.PROJECT_ROOT)
        study = os.path.split(relative_path)[0]
        if study in settings.ACTIVE_STUDIES:
            break
    
    return os.path.join(settings.REPORTS_TEMPLATE.format(study_name=study),
                        filename)
