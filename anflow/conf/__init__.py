from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
from importlib import import_module

from anflow.conf import global_settings

ENVIRONMENT_VARIABLE = "ANFLOW_SETTINGS_MODULE"

class Settings(object):

    def configure(self, defaults=global_settings):
        self.settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        
        for variable in dir(defaults):
            if variable.isupper():
                setattr(self, variable, getattr(defaults, variable))

        try:
            if not self.settings_module:
                raise ImportError
            mod = import_module(self.settings_module)
        except ImportError as e:
            raise ImportError("Could not import settings in '{}'. Is the "
                              "module on your path? Are there import errors "
                              "in the file?".format(self.settings_module))
        
        for variable in dir(mod):
            if variable.isupper():
                setattr(self, variable, getattr(mod, variable))

    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        object.__setattr__(self, attr, value)

settings = Settings()
