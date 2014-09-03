from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from anflow.lib.resamplers.base import Resampler



class Jackknife(Resampler):

    name = 'jackknife'

    def resample(self, data):

        N = len(data)
        if self.average:
            data_sum = sum(data)
            resampled_data = [(data_sum - datum) / (N - 1) for datum in data]
        else:
            resampled_data = [data[:i] + data[i+1:] for i in range(N)]
        return resampled_data

    def _central_value(self, datum, results, function):
        if self.do_resample:
            if self.average:
                return function(sum(datum.value) / len(datum.value))
            else:
                return function(datum.value)
        else:
            return function(datum.central_value)

    @staticmethod
    def error(data, central_value):

        N = len(data)
        deviations = map(lambda datum: (datum - central_value)**2, data)
        return ((N - 1) / N * sum(deviations))**0.5
