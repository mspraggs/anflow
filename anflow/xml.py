import importlib
import operator
import os

from anflow.data import Query
from anflow.parameters import add_sweep, add_spokes
from anflow.parsers import GuidedParser
from anflow.simulation import Simulation


def load_from_file(path, funcname):
    # TODO: implement
    pass


def parameters_from_elem(elem):
    """Recurses through the supplied xml element and builds a list of
    dictionaries containing parameters"""

    output = [{}]
    for subelem in elem:
        if subelem.tag in ["constant", "spoke", "sweep"]:
            name = subelem.get('name')
            try:
                value = eval(subelem.text.strip())
            except NameError:
                value = subelem.text.strip()

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


def query_from_elem(elem):
    """Creates a Query object from the specified xml element"""
    # TODO: Write test for this function
    output = []
    for subelem in elem:
        if subelem.tag == "constant":
            name = subelem.get('name')
            value = subelem.text.strip()
            try:
                value = eval(value)
            except NameError:
                pass
            output.append([Query(**{name: value})])
        elif subelem.tag in ["filter", "exclude"]:
            subqueries = query_from_elem(subelem)
            query = Query(*subqueries)
            query.connector = getattr(operator,
                                      "{}_".format(subelem.get('connector')))
            query.negate = subelem.tag == "exclude"
            output.append(query)

    return output


def input_from_elem(elem):
    """Retrieves the input tag and query from the xml element"""
    # TODO: Write test for this function
    input_tag = elem.find('./tag').text.string()
    for tag in ['filter', 'exclude']:
        query_elem = elem.find('./{}'.format(tag))
        if query_elem:
            break
    query = query_from_elem(query_elem)

    return input_tag, query


def parser_from_elem(sim, elem, data_root):
    """Takes part of an element tree and uses it to register a parser object
    with the specified simulation"""
    # Get the parameters
    parser_tag = elem.get("tag")
    parameters = parameters_from_elem(elem.find('./parameters'))
    # Get the loader function
    loader_elem = elem.find('./loader')
    modname = loader_elem.get('module')
    funcname = loader_elem.text.strip()
    mod = importlib.import_module(modname)
    loader_func = getattr(mod, funcname)
    # Get the path template
    path_template = elem.find('./path_template').text.strip()
    if data_root:
        path_template = os.path.join(data_root, path_template)
    # Get the collect statements
    collect = {}
    for subelem in elem.findall('./collect'):
        collect[subelem.get('name')] = eval(subelem.text.strip())

    # Now register the parser
    parser = GuidedParser(path_template, loader_func, parameters, **collect)
    sim.register_parser(parser_tag, parser)


def model_from_elem(sim, elem):
    """Register a model with the supplied simulation using the supplied
    xml element"""
    # TODO: Write test for this function
    model_tag = elem.get('tag')
    modname = elem.get('module')
    funcname = elem.get('function')
    mod = importlib.import_module(modname)
    func = getattr(mod, funcname)

    input_tag, query = input_from_elem(elem.find('./input'))

    sim.register_model(model_tag, func, input_tag)


def simulation_from_etree(tree, defaults={}):
    """Generates a simulation object using the parameters in the supplied
    ElementTree"""

    sim = Simulation()
    data_root = defaults.get('data_root')
    root = tree.getroot()

    for elem in root:
        if elem.tag == "data_root":
            data_root = elem.text.strip()
        elif elem.tag == "model":
            model_from_elem(sim, elem)
        elif elem.tag == "view":
            view_from_elem(sim, elem)
        elif elem.tag == "parser":
            parser_from_elem(sim, elem, data_root)

