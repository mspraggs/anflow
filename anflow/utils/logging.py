from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import logging
import inspect
from functools import wraps

def logger():
    """Returns a Logger object with path equal to the module, class and
    function in which this function is called"""

    stack = inspect.stack()
    # Move up the stack, looking for the function that called this function
    # We ignore functions that start with _ to circumvent decorators
    for frame in stack[1:]:
        if not frame[3].startswith("_"):
            obj = frame[0], frame[3]
            break

    try:
        names = [inspect.getmodule(obj[0]).__name__]
    except AttributeError:
        names = []
    try:
        names.append(obj[0].f_locals['self'].__class__.__name__)
    except KeyError:
        pass
    names.append(obj[1])
    return logging.getLogger(".".join(names))

def make_func_logger(f, args):

    # First construct a logger based on module, class and function names
    mod = inspect.getmodule(f).__name__
    names = [mod] if mod != "__main__" else []
    if (inspect.isclass(args[0].__class__)
        and "self" in inspect.getargspec(f).args):
        names.append(args[0].__class__.__name__)
    names.append(f.__name__)
    return logging.getLogger(".".join(names))

def merge_arguments(argspec, args, kwargs):

    if argspec.defaults == None:
        return kwargs
    else:        
        kwargs_defaults = dict(zip(argspec.args[-len(argspec.defaults):],
                                   argspec.defaults))
        kwargs_defaults.update(kwargs)

        for key, val in zip(argspec.args, args):
            try:
                kwargs_defaults.pop(key)
            except KeyError:
                pass

        return kwargs_defaults

class _Log(object):

    def __init__(self, message=None, ignore=()):
        self.init_message = message
        self.ignore=ignore + ("self",)

    def __call__(self, f):

        @wraps(f)
        def _wrapper(*args, **kwargs):

            logger = make_func_logger(f, args)

            if self.init_message != None:
                logger.info(self.init_message)
            
            argspec = inspect.getargspec(f)
            # List the arguments that don't have defaults
            self.print_args(zip(argspec.args, args), logger)

            # Now merge any default values with the kwargs and list these
            kwargs = merge_arguments(argspec, args, kwargs)
            self.print_args(kwargs.items(), logger)

            return f(*args, **kwargs)

        return _wrapper

    def print_args(self, args, logger):

        for key, val in args:
            if key in self.ignore or len(val.__repr__()) > 500:
                continue
            logger.info("{}: {}".format(key, val))

def Log(message=None, ignore=()):
    """Decorates a function so that its arguments are logged and outputted.

    Args:
      message (str, optional): Optional message to display before the body of
        the function is executed.
      ignore (tuple, optional): The names of any functions arguments that should
        not be outputted (e.g. if one of the arguments is an enormouse array).

    Returns:
      function: The decorated function.
        
    Examples:
      Here we create a random function, decorating it so the parameters are
      printed to the screen.

      >>> import logging
      >>> logging.basicConfig(level=logging.INFO)
      >>> import pyQCD
      >>> @pyQCD.Log("Now running the test function!", ignore=("x",))
      >>> def blah(x, y, z):
      ...     print(x, y, z)
      ...
      >>> blah(1, 2, 3)
      INFO:blah:Now running the test function!
      INFO:blah:y: 2
      INFO:blah:z: 3
      (1, 2, 3)

      You don't actually need to use parantheses or arguments with the Log
      decorator at all:

      >>> import logging
      >>> logging.basicConfig(level=logging.INFO)
      >>> import pyQCD
      >>> @pyQCD.Log
      >>> def blah(x, y, z):
      ...     print(x, y, z)
      ...
      >>> blah(1, 2, 3)
      INFO:blah:x: 1
      INFO:blah:y: 2
      INFO:blah:z: 3
      (1, 2, 3)
    """
    
    if callable(message):
        log = _Log()
        return log(message)
    else:
        def _wrapper(f):
            log = _Log(message, ignore)
            return log(f)
        return _wrapper
