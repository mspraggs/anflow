from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import os
from importlib import import_module
import warnings

from sqlalchemy import create_engine

from anflow.conf import global_settings
from anflow.db import Base, Session

ENVIRONMENT_VARIABLE = "ANFLOW_SETTINGS_MODULE"

class Settings(object):

    def configure(self, defaults=global_settings):
        self.settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        
        for variable in dir(defaults):
            if variable.isupper():
                setattr(self, variable, getattr(defaults, variable))

        if not self.settings_module:
            warnings.warn("{} environment variable not set, relying on default "
                          "settings only".format(ENVIRONMENT_VARIABLE))
        else:
            mod = import_module(self.settings_module)
            for variable in dir(mod):
                if variable.isupper():
                    setattr(self, variable, getattr(mod, variable))

        try:
            self.engine = create_engine(settings.DB_PATH)
            Base.metadata.bind = self.engine
            Session.configure(bind=self.engine)
            self.session = Session()
        except AttributeError:
            pass

    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        object.__setattr__(self, attr, value)

settings = Settings()
