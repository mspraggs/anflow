from __future__  import absolute_import

from itertools import product


def global_sweep(**kwargs):
    """Generate a list of dictionaries containing all possible combinations of
    the supplied parameters. Parameters should be specified using keywords
    with either single values or iterables."""
    parameters = [dict(zip(kwargs.keys(), items))
                  for items in product(*kwargs.values())]
    return parameters


def hub_and_spokes(base, **kwargs):
    """Generate a list of dictionaries all based on the supplied base
    dictionary. Each of the entries in this dictionary are then varied in turn
    using the supplied keyword arguments, which themselves should be
    iterables"""

    parameters = [base]
    for key, values in kwargs.items():
        for value in values:
            params = base.copy()
            params[key] = value
            parameters.append(params)

    return parameters