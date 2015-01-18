import operator

from anflow.data import Query
from anflow.parameters import (add_sweep, add_spokes)
from anflow.simulation import Simulation


def parameters_from_elem(elem):
    """Recurses through the supplied xml element and builds a list of
    dictionaries containing parameters"""

    output = [{}]
    for subelem in elem:
        if subelem.tag in ["constant", "spoke", "sweep"]:
            name = subelem.get('name')
            value = eval(subelem.text)

        if subelem.tag == "constant":
            for i, params in enumerate(output):
                output[i][name] = value
        elif subelem.tag == "sweep":
            output = add_sweep(output, **{name: value})
        elif subelem.tag == "spoke":
            output = add_spokes(output, **{name, value})
        elif subelem.tag in ["filter", "exclude"]:
            exclude_params = parameters_from_elem(subelem)
            for params in exclude_params:
                query = Query(**params)
                query.connector = getattr(operator,
                                          "{}_".format(query.get('connector')))
                query.negate = subelem.tag == "exclude"
                output = query.evaluate(output)


def simulation_from_etree(tree, defaults={}):
    """Generates a simulation object using the parameters in the supplied
    ElementTree"""

    sim = Simulation()
    data_root = defaults.get('data_root')
    root = tree.getroot()
    input_elems = []
    model_elems = []
    view_elems = []

    for elem in root:
        if elem.tag == "data_root":
            data_root = elem.text
        elif elem.tag == "model":
            model_from_elem(sim, elem)
        elif elem.tag == "view":
            view_from_elem(sim, elem)
        elif elem.tag == "input":
            input_from_elem(sim, elem)

    inputs = [input_from_elem(elem, data_root) for elem in input_elems]

