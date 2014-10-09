from __future__ import absolute_import

import os



class FileWrapper(object):
    """Lazy file loading wrapper"""

    def __init__(self, filename, loader):
        """Constructor"""

        self.filename = filename
        self.loader = loader
        self.timestamp = os.path.getmtime(filename)

    @property
    def data(self):
        try:
            return self._data
        except AttributeError:
            self._data = self.loader(self.filename)
            return self._data
