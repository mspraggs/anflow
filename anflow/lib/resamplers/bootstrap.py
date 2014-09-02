from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from anflow.lib.resamplers.base import Resampler



class Bootstrap(Resampler):

    name = 'bootstrap'

    @staticmethod
    def resample(data):

        N = len(data)
        binset = [np.random.randint(N, size=N).tolist() for i in range(N)]
        resampled_data = [sum([data[i] for i in bins]) / (N - 1)
                          for bins in binset]
        central_value = sum(resampled_data) / N
        return resampled_data, central_value

    @staticmethod
    def error(data, central_value):

        N = len(data)
        deviations = map(lambda datum: (datum - central_value)**2, data)
        return np.sqrt((N - 1) / N * sum(deviations))
