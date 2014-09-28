from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random

import pytest

from anflow.db.query import Manager
from anflow.core.wrappers import Datum



def my_resampler(datum, func):

    result = map(func, datum.value)
    centre = func(sum(datum.value))
    error = 0.0
    return result, centre, error

class TestModel(object):

    def test_meta(self, MyModel):

        attrs = ['id', 'value', 'central_value', 'error', 'timestamp', 'data',
                 '_params', 'abstract', 'main', 'input_stream', 'parameters',
                 'depends_on', 'resampler', 'model_name']
        for attr in attrs:
            assert hasattr(MyModel, attr)

        assert 'foo' in MyModel._params
        assert 'bar' in MyModel._params
        assert isinstance(MyModel.data, Manager)
        assert (MyModel.__mapper_args__['polymorphic_identity']
                == 'anflowMyModel')

    def test_constructor(self, MyModel):

        model_instance = MyModel(foo="blah", bar=0.5, some_var=5)
        assert model_instance.foo == "blah"
        assert model_instance.bar == 0.5
        assert model_instance.some_var == 5

    def test_paramsdict(self, MyModel):

        model = MyModel(foo="blah", bar=0.5, some_var=5)
        params = model.paramsdict()
        assert params == {'foo': 'blah', 'bar': 0.5, 'some_var': 5}

    def test_run(self, MyModel):

        div = random.randint(1, 10)
        models = MyModel.run(some_var=div)

        assert len(models) == len(MyModel.input_stream)
        for i, result in enumerate(models):
            assert result.value == i**2 // div
            assert result.foo == str(i)
            assert result.bar == 2 * i
            assert result.some_var == div

        MyModel.input_stream = [Datum({'foo': str(i), 'bar': 2 * i},
                                      [j + i for j in range(10)])
                                for i in range(10)]
        MyModel.resampler = staticmethod(my_resampler)

        models = MyModel.run(some_var=div)

        assert len(models) == len(MyModel.input_stream)

    def test_save(self, settings, MyModel):

        model = MyModel(foo="blahblah", bar=10.0)
        model.save()

        query = settings.session.query(MyModel)

        assert len(query.all()) == 1
        assert query.first().foo == "blahblah"
        assert query.first().bar == 10.0
        assert query.first().timestamp

        settings.session.delete(model)
        settings.session.commit()
