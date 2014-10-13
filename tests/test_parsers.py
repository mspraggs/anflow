from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from anflow.core.wrappers import Datum
from anflow.core.parsers.base import BaseParser
from anflow.core.parsers import BlindParser, GuidedParser

import importlib
import inspect
from itertools import product
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import shutil

import pytest
import numpy as np

from anflow.parsers import GuidedParser



@pytest.fixture
def data_to_parse(tmp_dir, request):

    try:
        os.makedirs(os.path.join(tmp_dir, "rawdata"))
    except OSError:
        pass
    data = np.arange(10)
    np.save(os.path.join(tmp_dir, "rawdata/data_a1_b2.npy"), data)

    request.addfinalizer(lambda: shutil.rmtree(os.path.join(tmp_dir, "rawdata"),
                                               ignore_errors=True))

    return data

class TestGuidedParser(object):

    def test_init(self, data_to_parse):
        """Test GuidedParser constructor"""

        template = "data_a{a}_b{b}.npy"
        
        params = [{'a': 1, 'b': 2}]
        def load_func(filepath, b):
            return np.load(filepath.format(b=b))
        
        parser = GuidedParser(template, load_func, parameters=params)

        assert parser.path_template == template
        assert hasattr(parser, 'config')
        assert parser.loader == load_func
        assert parser.collect == ['b']
