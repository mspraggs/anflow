from __future__  import absolute_import

from itertools import product
from xml.etree import ElementTree as ET


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


def parse_etree(etree, path):
    """Parses the supplied ElementTree, looking in the specified path for
    <parameters> tags from which to load dictionaries of parameters"""

    # Handle broken findall on ElementTree if ET.VERSION == 1.3.x
    if path.startswith('/') and ET.VERSION.split('.')[:2] == ['1', '3']:
        path = '.' + path

    ret = []
    for parameters in etree.iterfind(path):
        params_dict = {}
        for param_elem in parameters:
            params_dict[param_elem.tag] = eval(param_elem.text)
        ret.append(params_dict)
    return ret


def generate_etree(parameters, root_name):
    """Generate an xml Element using the specified list of parameters"""

    root = ET.Element(root_name)

    for params in parameters:
        node = ET.SubElement(root, 'parameters')
        for key, value in params.items():
            parameter = ET.SubElement(node, key)
            parameter.text = str(value)

    return root