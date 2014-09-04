
try:
    import cPickle as pickle
except:
    import pickle

import numpy as np
    
from anflow.core.data import Datum
from anflow.core.parsers.base import BaseParser
from anflow.core.parsers import BlindParser, GuidedParser

def blind_parse(filename):
    params = re.search(r'data_m(?P<mass>\d*\.\d*)\.(?P<config>\d+)\.pkl',
                       component_file).groupdict()
    with open(filename) as f:
        data = pickle.load(f)
    if params:
        return Datum(params, data, filename)
    else:
        return

def get_base_parser():
    return BaseParser()
    
def get_blind_parser():
    return BlindParser(blind_parse)

def get_guided_parser():
    return GuidedParser(guided_parse,
                        path_template="data_m{mass}.{config}.pkl",
                        mass=np.arange(0.1, 0.8, 0.1).tolist(),
                        config=range(100))
