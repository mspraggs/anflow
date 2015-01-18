from __future__  import absolute_import

from itertools import product
from xml.etree import ElementTree as ET


def add_sweep(base, **kwargs):
    """Generate a list of dictionaries containing all possible combinations of
    the supplied parameters, using the provided list as a base. Parameters
    should be specified using keywords with either single values or iterables.
    """

    output = []
    for params in base:
        for items in product(*kwargs.values()):
            params_to_add = params.copy()
            params_to_add.update(zip(kwargs.keys(), items))
            output.append(params_to_add)
    return output


def add_spokes(base, **kwargs):
    """Generate a list of dictionaries all based on the supplied base
    dictionaries. Each of the entries in the supplied list of dictionaries are
    varied in turn using the supplied keyword arguments, which themselves should
    be iterables"""

    output = []
    for params in base:
        output.append(params)
        for key, values in kwargs.items():
            for value in values:
                params_copy = params.copy()
                params_copy[key] = value
                output.append(params_copy)
    return output


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