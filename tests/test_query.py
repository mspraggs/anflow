from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
import pytest

from anflow.conf import settings
from anflow.db.query import DataSet, Manager



@pytest.fixture(scope='session')
def populatedb(MyModel, settings, request):

    models = []
    for i in range(10):
        new_model = MyModel(foo="tortoise{}".format(i),
                            bar=float(i) / 2,
                            some_var=i)
        new_model.save()
        models.append(new_model)

    def fin():
        for model in models:
            settings.session.delete(model)
        settings.session.commit()
        
    request.addfinalizer(fin)

@pytest.fixture
def dataset(populatedb, MyModel, settings):
    return DataSet(settings.session.query(), MyModel)

class TestManager(object):
    
    def test_constructor(self, MyModel):
        manager = Manager(MyModel)

class TestDataSet(object):

    def test_constructor(self, dataset, MyModel):
        assert dataset.model_class == MyModel
        assert MyModel in dataset.query._entities[0].entities

    def test_all(self, dataset):
        results = dataset.all()
        assert len(set(results)) == 10
            
    def test_filter(self, dataset):

        results = dataset.filter(some_var=1)
        assert isinstance(results, DataSet)
        assert len(results.query.all()) == 1
        assert results.query.first().some_var == 1

        results = dataset.filter(some_var__gt=1)
        assert len(results.query.all()) == 8
        for result in results.query:
            assert result.some_var > 1

        results = dataset.filter(some_var__gte=1)
        assert len(results.query.all()) == 9
        for result in results.query:
            assert result.some_var >= 1

        results = dataset.filter(some_var__lt=1)
        assert len(results.query.all()) == 1
        for result in results.query:
            assert result.some_var < 1

        results = dataset.filter(some_var__lte=1)
        assert len(results.query.all()) == 2
        for result in results.query:
            assert result.some_var <= 1

        results = dataset.filter(bar__aprx=0.5)
        assert len(results.query.all()) == 1
        assert np.allclose(results.query.first().bar, 0.5)
