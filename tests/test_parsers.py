from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

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

from anflow.data import FileWrapper
from anflow.parsers import GuidedParser, Parser



@pytest.fixture
def data_to_parse(tmp_dir, request):

    try:
        os.makedirs(os.path.join(tmp_dir, "rawdata"))
    except OSError:
        pass
    data = np.arange(10)
    np.save(os.path.join(tmp_dir, "rawdata/data_a1_b2.npy"), data)

    template = os.path.join(tmp_dir, "rawdata/data_a{a}_b{b}.npy")
    
    params = {'a': [1], 'b': [2]}
    def load_func(filepath, b):
        return np.load(filepath.format(b=b[0]))
        
    parser = GuidedParser(template, load_func, parameters=params)

    request.addfinalizer(lambda: shutil.rmtree(os.path.join(tmp_dir, "rawdata"),
                                               ignore_errors=True))

    return {'data': data, 'parser': parser,
            'rawdata_dir': os.path.join(tmp_dir, 'rawdata'),
            'template': template, 'load_func': load_func,
            'params': params}

class TestParser(object):

    def test_init(self):
        """Parser constructor test"""
        parser = Parser()
        assert hasattr(parser, 'parsed_data')
        assert hasattr(parser, '__iter__')
        assert hasattr(parser, '__len__')
        assert hasattr(parser, 'populate')
        assert not parser.populated
        assert len(parser) == 0

    def test_populate(self):
        """Parser.populate test"""
        parser = Parser()
        with pytest.raises(NotImplementedError):
            parser.populate()

    def test_iter(self):
        """Parser.__iter__ test"""
        parser = Parser()
        with pytest.raises(NotImplementedError):
            for datum in parser:
                pass

    def test_len(self):
        """Parser.__len__ test"""
        parser = Parser()
        assert len(parser) == 0

class TestGuidedParser(object):

    def test_init(self, data_to_parse):
        """Test GuidedParser constructor"""

        parser = data_to_parse['parser']

        assert parser.path_template == data_to_parse['template']
        assert parser.loader == data_to_parse['load_func']
        assert parser.collect == ['b']
        assert parser.populated == False
        assert hasattr(parser, 'parsed_data')

    def test_populate(self, data_to_parse):
        """Test GuidedParser"""
        
        parser = data_to_parse['parser']
        parser.populate()

        assert len(parser.parsed_data) == 1
        assert isinstance(parser.parsed_data[0], FileWrapper)
        assert (parser.parsed_data[0].data == data_to_parse['data']).all()
        assert parser.parsed_data[0].params == {'a': 1}
        assert parser.populated

    def test_iter(self, data_to_parse):
        """Test GuidedParser.__iter__ and GuidedParser.next"""

        parser = data_to_parse['parser']

        for datum in parser:
            assert datum.params == {'a': 1}
            assert (datum.data == data_to_parse['data']).all()

        assert parser.populated
