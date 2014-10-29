from __future__ import absolute_import

import logging
import inspect
from functools import wraps


def logger():
    """Returns a Logger object with path equal to the module, class and
    function in which this function is called"""

    stack = inspect.stack()
    # Move up the stack, looking for the function that called this function
    # We ignore functions that start with _ to circumvent decorators
    for frame, filename, lineno, funcname, lines, line_index in stack[1:]:
        if not funcname.startswith("_"):
            break

    try:
        names = [inspect.getmodule(frame).__name__]
    except AttributeError:
        names = []
    try:
        # Try to get
        names.append(frame.f_locals['self'].__class__.__name__)
    except KeyError:
        pass
    names.append(funcname)
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
        self.ignore = ignore + ("self",)

    def __call__(self, f):

        @wraps(f)
        def _wrapper(*args, **kwargs):
            log = logger()

            if self.init_message:
                log.info(self.init_message)

            argspec = inspect.getargspec(f)
            # List the arguments that don't have defaults
            self.print_args(zip(argspec.args, args), log)

            # Now merge any default values with the kwargs and list these
            kwargs = merge_arguments(argspec, args, kwargs)
            self.print_args(kwargs.items(), log)

            return f(*args, **kwargs)

        return _wrapper

    def print_args(self, args, log):

        for key, val in args:
            if key in self.ignore or len(val.__repr__()) > 500:
                continue
            log.info("{}: {}".format(key, val))


def Log(message=None, ignore=()):
    """Decorates a function so that its arguments are logged and outputted."""

    if callable(message):
        log = _Log()
        return log(message)
    else:
        def _wrapper(f):
            log = _Log(message, ignore)
            return log(f)

        return _wrapper
