from __future__ import absolute_import

import importlib
import operator
import os
from xml.etree.ElementTree import ParseError

from anflow.data import Query
from anflow.parameters import add_sweep, add_spokes
from anflow.parsers import GuidedParser
from anflow.simulation import Simulation


def load_from_file(path, funcname):
    # TODO: implement
    pass


def find_or_error(elem, path):
    """Find the specified path in the supplied element, and fail if it doesn't
    exist"""
    # TODO: Make test
    child_elem = elem.find(path)
    if child_elem is None:
        raise ParseError("Cannot find path {} in {}".format(path, elem))
    return child_elem


def get_func_and_tag(elem):
    """Gets the function and the tag from the supplied elems attributes"""
    # TODO: Write test for this function
    # TODO: Enable gathering from file that isn't in path
    tag = elem.attrib['tag']
    modname = elem.attrib['module']
    funcname = elem.attrib['function']
    mod = importlib.import_module(modname)
    return tag, getattr(mod, funcname)


def parameters_from_elem(elem):
    """Recurses through the supplied xml element and builds a list of
    dictionaries containing parameters"""

    if elem is None:
        return None

    output = [{}]
    for subelem in elem:
        if subelem.tag in ["constant", "spoke", "sweep"]:
            name = subelem.attrib['name']
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
            query = query_from_elem(subelem)
            query.connector = getattr(operator,
                                      "{}_".format(subelem.attrib['connector']))
            query.negate = subelem.tag == "exclude"
            output = query.evaluate(output)

    return output


def query_from_elem(elem):
    """Creates a Query object from the specified xml element"""

    if elem is None:
        return None

    output = []
    for subelem in elem:
        if subelem.tag == "constant":
            name = subelem.attrib['name']
            value = subelem.text.strip()
            try:
                value = eval(value)
            except NameError:
                pass
            output.append(Query(**{name: value}))
        elif subelem.tag in ["filter", "exclude"]:
            query = query_from_elem(subelem)
            query.connector = getattr(operator,
                                      "{}_".format(subelem.attrib['connector']))
            query.negate = subelem.tag == "exclude"
            output.append(query)
    return Query(*output)


def input_from_elem(elem):
    """Retrieves the input tag and query from the xml element"""
    input_tag = find_or_error(elem, './tag').text.strip()
    for tag in ['filter', 'exclude']:
        query_elem = elem.find('./{}'.format(tag))
        if query_elem is not None:
            break
    query = query_from_elem(query_elem)

    return input_tag, query


def parser_from_elem(sim, elem, data_root):
    """Takes part of an element tree and uses it to register a parser object
    with the specified simulation"""
    # Get the parameters
    parser_tag = elem.attrib["tag"]
    parameters = parameters_from_elem(find_or_error(elem, './parameters'))
    # Get the loader function
    loader_elem = find_or_error(elem, './loader')
    modname = loader_elem.attrib['module']
    funcname = loader_elem.text.strip()
    mod = importlib.import_module(modname)
    loader_func = getattr(mod, funcname)
    # Get the path template
    path_template = find_or_error(elem, './path_template').text.strip()
    if data_root:
        path_template = os.path.join(data_root, path_template)
    # Get the collect statements
    collect = {}
    for subelem in elem.findall('./collect'):
        collect[subelem.attrib['name']] = eval(subelem.text.strip())

    # Now register the parser
    parser = GuidedParser(path_template, loader_func, parameters, **collect)
    sim.register_parser(parser_tag, parser)


def model_from_elem(sim, elem):
    """Register a model with the supplied simulation using the supplied
    xml element"""
    model_tag, func = get_func_and_tag(elem)
    input_tag, query = input_from_elem(find_or_error(elem, './input'))
    parameters = parameters_from_elem(elem.find('./parameters'))

    load_only = True if elem.find('./load_only') else False
    sim.register_model(model_tag, func, input_tag, load_only=load_only)
    return model_tag, parameters, query


def view_from_elem(sim, elem):
    """Register a view with the supplied simulation using the supplied xml
    element"""
    view_tag, func = get_func_and_tag(elem)

    queries = {}
    input_tags = []
    for subelem in elem.findall("./input"):
        tag, query = input_from_elem(subelem)
        input_tags.append(tag)
        queries[tag] = query

    parameters = parameters_from_elem(elem.find('./parameters'))

    sim.register_view(view_tag, func, input_tags)
    return view_tag, parameters, queries


def simulation_from_etree(tree, simname):
    """Generates a simulation object using the parameters in the supplied
    ElementTree"""
    # TODO: Add test for this function
    sim = Simulation("")
    tree.xinclude()
    root = tree.getroot()

    queries = {}
    parameters = {}
    for elem in root:
        if elem.tag == "data_root":
            data_root = elem.text.strip()
        elif elem.tag == "model":
            tag, params, query = model_from_elem(sim, elem)
            queries[tag] = query
            parameters[tag] = params
        elif elem.tag == "view":
            tag, params, query = view_from_elem(sim, elem)
            queries[tag] = query
            parameters[tag] = params
        elif elem.tag == "parser":
            parser_from_elem(sim, elem, data_root)

    return sim, parameters, queries