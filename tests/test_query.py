from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

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
