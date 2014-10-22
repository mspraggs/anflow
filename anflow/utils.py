from __future__ import absolute_import

import inspect
import os
import pkgutil
import sys



def get_root_path(import_name):
    """Gets the root path of a project based on the supplied module.
    This works in pretty much the same way to the function in flask.
    The implementation is identical."""

    # First look in the list of imported modules
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, '__file__'):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Try to get the module loader and use that to retrieve the filename
    loader = pkgutil.get_loader(import_name)

    # If there's no loader or we're running in interactive mode, use cwd
    if not loader or import_name == "__main__":
        return os.getcwd()

    # If there *is* as loader, use its filename
    if hasattr(loader, 'get_filename'):
        filepath = loader.get_filename(import_name)
    else:
        # Argh, no get_filename function, just import instead
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, '__file__', None)

        if not filepath:
            raise RuntimeError("Cannot get root path for import name {}."
                               .format(import_name))

    # Now return the directory path the import_name module is in
    return os.path.dirname(os.path.abspath(filepath))

def get_dependency_files(obj, top, n=10):
    """Gets a list of files that obj depends on in some way that are under
    the directory top"""
    if n == 0:
        return []
    mod = inspect.getmodule(obj)
    try:
        filename = inspect.getsourcefile(mod)
    except TypeError:
        filename = None
    else:
        if filename:
            filename = os.path.abspath(filename)
            relpath = os.path.relpath(filename, top)
            if relpath.startswith('..'):
                filename = None
    out = []
    if filename:
        out.append(filename)
        for name, attr in mod.__dict__.items():
            out.extend(get_dependency_files(attr, top, n - 1))
    return list(set(out))
