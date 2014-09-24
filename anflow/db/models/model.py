from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.db.models.base import BaseModel



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
    history = relationship("History", backref=backref('anflowHistory',
                                                      order_by=id))

    timestamp = Column(DateTime, default=datetime.datetime.now)

    @classmethod
    def run(cls, *args, **kwargs):
        """Runs the measurement on the files returned by the specified
        input_stream"""

        log = logger()

        mainargspec = inspect.getargspec(cls.main)
        results = []
        study_name = get_study(cls.__module__)

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

    def paramsdict(self):
        out = {}
        for name in self._params:
            out.update({name: getattr(self, name)})
        return out
