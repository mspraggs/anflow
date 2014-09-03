from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from anflow.lib.resamplers.base import Resampler



class Bootstrap(Resampler):

    name = 'bootstrap'

    def resample(self, data):

        N = len(data)
        self.binset = [np.random.randint(N, size=N).tolist() for i in range(N)]
        resampled_data = [[data[i] for i in bins] for bins in self.binset]
        if self.average:
            return [sum(datum) / len(datum) for datum in resampled_data]
        else:
            return resampled_data

    def _central_value(self, datum, results, function):
        return sum(results) / len(results)
    
    @staticmethod
    def error(data, central_value):

        N = len(data)
        deviations = map(lambda datum: (datum - central_value)**2, data)
        return np.sqrt(sum(deviations) / N)
