from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from datetime import datetime

import numpy as np
import pytest

from anflow.conf import settings
from anflow.db.models import History
from anflow.db.query import DataSet, Manager



@pytest.fixture(scope='session')
def populatedb(MyModel, settings, request):

    run = History()
    models = []
    for i in range(2):
        new_model = MyModel(foo="tortoise{}".format(i),
                            bar=float(i) / 2,
                            some_var=i,
                            history=run)
        models.append(new_model)
    run.save()
    run = History()
    for i in range(2, 5):
        new_model = MyModel(foo="tortoise{}".format(i),
                            bar=float(i) / 2,
                            some_var=i,
                            history=run)
    run.save()
    for i in range(5, 10):
        new_model = MyModel(foo="tortoise{}".format(i),
                            bar=float(i) / 2,
                            some_var=i)
        new_model.save()

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

    def test_count(self, dataset):
        assert dataset.count() == 10
            
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

        # Try a couple of filters in parallel
        results = dataset.filter(some_var__gte=1, some_var__lt=9)
        assert len(results.query.all()) == 8
        for result in results.query:
            assert 1 <= result.some_var < 9

        results = dataset.filter(some_var__gt=1, bar__aprx=2.5)
        assert len(results.query.all()) == 1
        for result in results.query:
            assert result.some_var > 1
            assert np.allclose(result.bar, 2.5)

    def test_order_by(self, dataset):

        results = dataset.order_by('some_var')
        for result in results.query:
            try:
                assert last_result.some_var <= result.some_var
            except NameError:
                pass
            last_result = result
            
        results = dataset.order_by('-some_var')
        for result in results.query:
            try:
                assert last_result.some_var >= result.some_var
            except NameError:
                pass
            last_result = result

    def test_history(self, dataset):

        history = History.data.all()
        assert len(dataset.history(0).query.all()) == 2
        assert len(dataset.history(1).query.all()) == 3
        assert len(dataset.history(-2).query.all()) == 2
        assert len(dataset.history(-1).query.all()) == 3

    def test_latest(self, dataset, MyModel):

        latest = dataset.latest()
        assert len(latest.query.all()) == 5
        for result in latest.query:
            assert result.some_var > 3

        new_run = History(start_time=datetime.now())
        for datum in dataset.query.filter(MyModel.history == None):
            datum.history = new_run
        new_run.save()

        latest = dataset.latest()
        assert len(latest.query.all()) == 5
        for result in latest.query:
            assert result.some_var > 3

        latest = dataset.latest(orphans_only=True)
        assert len(latest.query.all()) == 0

    def test_first(self, dataset):

        assert dataset.first() is not None
