from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import random
import string

from anflow.core.data import Datum, DataSet



class TestDatum(object):

    def test_constructor(self, settings):
        randoms = ([random.randint(0, 100) for i in range(10)]
                   + [10 * random.random() for i in range(10)])
        params = dict([("".join(random.sample(string.lowercase, 5)),
                        random.choice(randoms))
                        for i in range(10)])
        random.shuffle(randoms)
        filename = "".join(random.sample(string.lowercase, 10))
        datum = Datum(params, randoms, filename)

        assert datum.value == randoms
        assert datum.paramsdict() == params
        assert datum._timestamp == None
        assert datum._filename == filename
        
        for key, value in params.items():
            assert getattr(datum, key) == value
