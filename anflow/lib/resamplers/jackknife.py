from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from anflow.lib.resamplers.base import Resampler



class Jackknife(Resampler):

    name = 'jackknife'

    @staticmethod
    def resample(data):

        N = len(data)
        data_sum = sum(data)
        central_value = data_sum / N

        resampled_data = [(data_sum - datum) / (N - 1) for datum in data]
        return resampled_data, central_value

    @staticmethod
    def error(data, central_value):

        N = len(data)
        deviations = map(lambda datum: (datum - central_value)**2, data)
        return ((N - 1) / N * sum(deviations))**0.5
