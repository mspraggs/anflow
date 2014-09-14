from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import Column, String, Float

import pytest

from anflow.db import models
from anflow.db.data import Datum
from anflow.db.models.manager import Manager

@pytest.fixture()
def MyModel(settings):

    class MyModel(models.Model):

        input_stream = [Datum({'foo': i, 'bar': 2 * i}, i**2)
                        for i in range(10)]
        foo = Column(String)
        bar = Column(Float)

        @staticmethod
        def main(data, foo, bar):
            return data / 2

    return MyModel

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
                == 'table_MyModel')
