from __future__ import absolute_import
from __future__ import unicode_literals

import importlib
import os
import shelve
import shutil
import sys
import time

import pytest

from anflow import Simulation
from anflow.data import DataSet, Datum, Query

from .utils import delete_shelve_files, count_shelve_files


@pytest.fixture
def sim(tmp_dir, request):

    settings = {}
    settings['RESULTS_DIR'] = os.path.join(tmp_dir, "results")
    settings['REPORTS_DIR'] = os.path.join(tmp_dir, "reports")

    input_data = []
    input_parameters = []
    for a, b in [(x, y) for x in range(5) for y in range(2)]:
        params = {'a': a, 'b': b}
        input_parameters.append(params)
        datum = Datum(params, 1.0, tmp_dir + '/')
        datum.save()
        input_data.append(datum)

    sim = Simulation("testsim", root_path=tmp_dir)
    sim.config.from_dict(settings)

    with open(os.path.join(tmp_dir, '__init__.py'), 'a') as f:
        pass
    with open(os.path.join(tmp_dir, "functions.py"), 'w') as f:
        f.write('def func1(data): return data\n')
        f.write('def func2(data): return data\n')
        f.write('def func3(data): pass\n')
    sys.path.insert(0, tmp_dir)
    module = importlib.import_module('functions')
    
    def fin():
        delete_shelve_files(tmp_dir + "/a1.pkl")
        for filename in ['__init__.py', 'functions.py']:
            try:
                os.unlink(os.path.join(tmp_dir, filename))
            except OSError:
                pass
        shutil.rmtree(settings['RESULTS_DIR'], ignore_errors=True)
        shutil.rmtree(settings['REPORTS_DIR'], ignore_errors=True)
        sys.path.remove(tmp_dir)
    request.addfinalizer(fin)
    
    return {'simulation': sim, 'input_data': input_data,
            'module': module, 'parameters': input_parameters}

@pytest.fixture
def run_sim(tmp_dir, sim, request):

    simulation = sim['simulation']
    def model(data):
        return data
    model.results = DataSet([{'a': 1}], simulation.config,
                            os.path.join(tmp_dir, 'results', 'model_'))
    model.results._parent = model
    simulation.models = {'model': (model, sim['input_data'], None)}

    os.makedirs(os.path.join(tmp_dir, "results"))
    shelf = shelve.open(tmp_dir + "/results/model_a1.pkl")
    shelf[b'params'] = {'a': 1}
    shelf[b'data'] = 1.0
    shelf[b'timestamp'] = time.time()
    shelf.close()

    def fin():
        shutil.rmtree(simulation.config.REPORTS_DIR, ignore_errors=True)
    request.addfinalizer(fin)

    return {'simulation': simulation, 'model': model,
            'module': sim['module']}

class TestSimulation(object):

    def test_init(self, sim, tmp_dir):
        """Test object constructor"""
        assert hasattr(sim['simulation'], 'models')
        assert hasattr(sim['simulation'], 'views')
        assert hasattr(sim['simulation'], 'config')
        assert sim['simulation'].import_name == "testsim"
        assert sim['simulation'].root_path == tmp_dir
        assert sim['simulation'].config.RESULTS_DIR == os.path.join(tmp_dir,
                                                                    "results")
        assert sim['simulation'].config.REPORTS_DIR == os.path.join(tmp_dir,
                                                                    "reports")

    def test_register_model(self, sim):
        """Test Simulation.register_model"""

        simulation = sim['simulation']
        def some_func(data):
            pass
        simulation.register_model("some_func", some_func, "input_tag")

        assert simulation.models['some_func'].func == some_func
        assert simulation.models['some_func'].input_tag == "input_tag"
        assert simulation.models['some_func'].path_template is None

    def test_register_view(self, run_sim):
        """Test Simulation.register_view"""
        
        simulation = run_sim['simulation']
        def some_view(data):
            pass
        simulation.register_view('some_view', some_view, ('some_input',))

        assert simulation.views['some_view'].func == some_view
        assert simulation.views['some_view'].input_tags == ('some_input',)
        assert simulation.views['some_view'].output_dir is None

    def test_run_model(self, sim, tmp_dir):
        """Test Simulation.run_model"""
        
        simulation = sim['simulation']
        @simulation.register_model(input_data=sim['input_data'])
        def func1(data):
            return data
            
        decorator = simulation.register_model(input_data=func1.results,
                                              query=Query(a=1))
        func2 = sim['module'].func2
        func2 = decorator(func2)

        result = simulation.run_model('func1')
        for params in sim['parameters']:
            fname = 'a{a}_b{b}.pkl'.format(**params)
            assert count_shelve_files(os.path.join(tmp_dir, "results",
                                                   'func1', fname)) > 0
        assert result
        result = simulation.run_model('func2')
        for params in sim['parameters']:
            fname = 'a{a}_b{b}.pkl'.format(**params)
            if params['a'] == 1:
                assert count_shelve_files(os.path.join(tmp_dir, "results",
                                                       'func2', fname)) > 0
            else:
                assert count_shelve_files(os.path.join(tmp_dir, "results",
                                                       'func2', fname)) == 0
        assert result

        result = simulation.run_model('func2')
        assert not result
        result = simulation.run_model('func2', force=True)
        assert result

    def test_run_view(self, run_sim, tmp_dir):
        """Test Simulation.run_model"""

        simulation = run_sim['simulation']
        
        def some_view(data):
            with open("some_file", 'w') as f:
                f.write(data['model'].first().params['a'].__repr__() + "\n")
        run_sim['module'].func3 = some_view
                
        decorator = simulation.register_view((run_sim['model'],),
                                             parameters=[{'a': 1}])
        func3 = run_sim['module'].func3
        func3 = decorator(func3)

        result = simulation.run_view('some_view')
        assert result
        assert os.path.exists(os.path.join(tmp_dir, 'reports/some_view/'
                                                    'some_file'))
        with open(os.path.join(tmp_dir, 'reports/some_view/some_file')) as f:
            lines = f.readlines()
        assert len(lines) == 1
        assert lines[0] == '1\n'
        
        result = simulation.run_view('some_view')
        assert not result

    def test_run(self, sim, tmp_dir):
        """Test Simulation.run"""
        simulation = sim['simulation']
        decorator = simulation.register_model(input_data=sim['input_data'])
        func1 = sim['module'].func1
        func1 = decorator(func1)
        decorator = simulation.register_model(input_data=func1.results)
        func2 = sim['module'].func2
        func2 = decorator(func2)
        
        simulation.run()
        for params in sim['parameters']:
            fname = 'a{a}_b{b}.pkl'.format(**params)
            assert count_shelve_files(os.path.join(tmp_dir, "results",
                                                   'func1', fname)) > 0
            assert count_shelve_files(os.path.join(tmp_dir, "results",
                                                   'func2', fname)) > 0

    def test_dependencies(self, sim, tmp_dir):
        """Test Simulation.dependencies"""
        simulation = Simulation('blah')
        @simulation.register_model(input_data=sim['input_data'])
        def func1(data):
            return data

        simulation2 = sim['simulation']
        decorator = simulation2.register_model(input_data=func1.results)
        func2 = sim['module'].func2
        func2 = decorator(func2)

        assert simulation2.dependencies == [simulation]