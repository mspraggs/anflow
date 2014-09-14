
try:
    import cPickle as pickle
except ImportError:
    import pickle
import re

import numpy as np
    
from anflow.db.data import Datum
from anflow.core.parsers.base import BaseParser
from anflow.core.parsers import BlindParser, GuidedParser

def blind_parse(filename):
    params = re.search(r'data_m(?P<mass>\d*\.\d*)\.(?P<config>\d+)\.pkl',
                       filename).groupdict()
    with open(filename) as f:
        data = pickle.load(f)
    if params:
        return params, data
    else:
        return

def guided_parse(path_template):
    with open(path_template) as f:
        data = pickle.load(f)
    return data

def get_base_parser():
    return BaseParser()
    
def get_blind_parser():
    return BlindParser(blind_parse)

def get_guided_parser():
    return GuidedParser(guided_parse,
                        path_template="data_m{mass}.{config}.pkl",
                        mass=np.arange(0.1, 0.8, 0.1).tolist(),
                        config=range(100))
