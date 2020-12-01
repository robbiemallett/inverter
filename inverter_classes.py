from inverter_tools import check_valid_bounds
import numpy as np

class MyTakeStep(object):
    def __init__(self, bounds, stepsize=1):
        self.stepsize = stepsize
        self.bounds = bounds

    def __call__(self, x):
        s = self.stepsize
        for i, b in enumerate(self.bounds):
            b_r = abs(b[1] - b[0])
            x[i] += np.random.uniform(-b_r * s, b_r * s)
        return x

class MyBounds(object):
    def __init__(self, bounds):
        self.bounds = bounds

    def __call__(self, **kwargs):
        params = kwargs["x_new"]
        valid_bounds = check_valid_bounds(params, self.bounds)
        return valid_bounds

