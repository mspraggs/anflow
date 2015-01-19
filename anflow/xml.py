import importlib
import operator
import os

from anflow.data import Query
from anflow.parameters import add_sweep, add_spokes
from anflow.parsers import GuidedParser
from anflow.simulation import Simulation


def parameters_from_elem(elem):
    """Recurses through the supplied xml element and builds a list of
    dictionaries containing parameters"""

    output = [{}]
    for subelem in elem:
        if subelem.tag in ["constant", "spoke", "sweep"]:
            name = subelem.get('name')
            try:
                value = eval(subelem.text)
            except NameError:
                value = subelem.text

        if subelem.tag == "constant":
            for i, params in enumerate(output):
                output[i][name] = value
        elif subelem.tag == "sweep":
            output = add_sweep(output, **{name: value})
        elif subelem.tag == "spoke":
            output = add_spokes(output, **{name, value})
        elif subelem.tag in ["filter", "exclude"]:
            subparams = parameters_from_elem(subelem)
            for params in subparams:
                query = Query(**params)
                query.connector = getattr(operator,
                                          "{}_".format(subelem.get('connector')))
                query.negate = subelem.tag == "exclude"
                output = query.evaluate(output)

    return output


def parser_from_elem(sim, elem, data_root):
    """Takes part of an element tree and uses it to register a parser object
    with the specified simulation"""
    # Get the parameters
    parser_tag = elem.get("tag")
    parameters = parameters_from_elem(elem.find('./parameters'))
    # Get the loader function
    loader_elem = elem.find('./loader')
    modname = loader_elem.get('module')
    funcname = loader_elem.text
    mod = importlib.import_module(modname)
    loader_func = getattr(mod, funcname)
    # Get the path template
    path_template = loader_elem.find('./path_template').text
    if data_root:
        path_template = os.path.join(data_root, path_template)
    # Get the collect statements
    collect = {}
    for subelem in elem.findall('./constant'):
        collect[subelem.get('name')] = eval(elem.text)

    # Now register the parser
    parser = GuidedParser(path_template, loader_func, parameters, **collect)
    sim.register_parser(parser_tag, parser)


def simulation_from_etree(tree, defaults={}):
    """Generates a simulation object using the parameters in the supplied
    ElementTree"""

    sim = Simulation()
    data_root = defaults.get('data_root')
    root = tree.getroot()

    for elem in root:
        if elem.tag == "data_root":
            data_root = elem.text
        elif elem.tag == "model":
            model_from_elem(sim, elem)
        elif elem.tag == "view":
            view_from_elem(sim, elem)
        elif elem.tag == "parser":
            parser_from_elem(sim, elem, data_root)

