from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from pytest

from anflow.db.query import Manager



@pytest.fixture(scope='session')
def populatedb(MyModel):
    
    for i in range(10):
        new_model = MyModel(foo="tortoise{}".format(i),
                            bar=float(i) / 2,
                            some_var=i)
        new_model.save()
