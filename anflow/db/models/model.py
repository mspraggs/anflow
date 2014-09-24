from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import datetime
from functools import partial
import inspect
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sys

from sqlalchemy import Column, DateTime, ForeignKey, Integer, PickleType
from sqlalchemy.orm import deferred

from anflow.db.models.base import BaseModel
from anflow.db.models.history import History
from anflow.utils.logging import Log, logger



class Model(BaseModel):

    abstract = False
    main = None # The function that encapsulates the model behaviour
    input_stream = None # The raw data to feed into the model
    parameters = None # A list of additional parameters to feed the model
    depends_on = None # A list of models this model depends on
    resampler = None # The resampler object that'll do the resampling

    value = deferred(Column(PickleType))
    central_value = deferred(Column(PickleType))
    error = deferred(Column(PickleType))
    history_id = Column(Integer, ForeignKey('anflowHistory.id'))
    timestamp = Column(DateTime, default=datetime.datetime.now)

    @classmethod
    def run(cls, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        log = logger()

        mainargspec = inspect.getargspec(cls.main)
        results = []

        for datum in cls.input_stream:
            # Combine parameters
            all_params = dict(zip(mainargspec.args, args))
            all_params.update(kwargs)
            all_params.update(datum.paramsdict())
            main_partial = partial(Log("Running model function {}.main"
                                       .format(cls.__class__.__name__))
                                   (cls.main), **all_params)

            if cls.resampler:
                try:
                    result, centre, error = cls.resampler(datum, main_partial)
                except:
                    log.critical("Oh noes! "
                                 "Your main function or resampler raised an "
                                 "exception!")
                    raise
                results.append(cls(value=result, central_value=centre,
                                   error=error, **all_params))
            else:
                try:
                    result = main_partial(datum.value)
                except:
                    log.critical("Oh noes! "
                                 "Your main function raised an exception!")
                    raise
                results.append(cls(value=result, **all_params))

        return results

    def save(self):
        """Save the model to the database"""

        size = 0
        for value in self.paramsdict().values():
            size += sys.getsizeof(value)
        for item in [self.value, self.central_value, self.error]:
            size += len(pickle.dumps(item))
        log = logger()
        log.info("Saving {} bytes, {} MB".format(size, size / 1024**2))

        BaseModel.save(self)

    def paramsdict(self):
        out = {}
        for name in self._params:
            out.update({name: getattr(self, name)})
        return out
