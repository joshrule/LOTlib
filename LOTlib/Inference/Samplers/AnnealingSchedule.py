"""
Annealing Schedules

These are various schedules for annealing parameters.

NOTE: "skip" steps are all run at the same temperature!
"""
from LOTlib.Miscellaneous import self_update
from math import sin, pi, log, pow, exp


class AnnealingSchedule:
    """
    A class to represent an annealing schedule. Should be subclassed.
    """
    def __init__(self):
        raise NotImplementedError

    def __iter__(self):
        return self


class ConstantSchedule(AnnealingSchedule):
    def __init__(self, k):
        self.k = k

    def next(self):
        return self.k


class InverseSchedule(AnnealingSchedule):
    """
    Temperature = max/(scale*time)
    """
    def __init__(self, max, scale):
        self_update(self, locals())
        self.ticks = 0

    def next(self):
        self.ticks += 1
        return self.max / (self.scale*self.ticks)


class ExponentialSchedule(AnnealingSchedule):
    """
    Temperature = c * alpha^t
    """
    def __init__(self, c, alpha):
        self_update(self, locals())
        self.ticks = 0

    def next(self):
        self.ticks += 1
        return self.c * pow(self.alpha, self.ticks)


class SinSchedule(AnnealingSchedule):
    """
    Let's go crazy -- search at various temperatures
    Temperature = min + (max-min)*sin(2*pi*time/period)
    """
    def __init__(self, min, max, period):
        assert max > min
        assert period > 0.
        self_update(self, locals())
        self.ticks = 0  # how many times have we called next?

    def next(self):
        self.ticks += 1
        return \
            self.min + \
            (self.max-self.min) * \
            (1. + sin(self.ticks * 2 * pi / self.period))/2.


class LogSinSchedule(SinSchedule):
    """
    Let's go crazy -- search at various temperatures -- on a log ladder
    Temperature = min + (max-min)*sin(2*pi*time/period)
    """
    def __init__(self, min, max, period):
        SinSchedule.__init__(self, log(min), log(max), period)

    def next(self):
        return exp(SinSchedule.next(self))


class InverseLogSchedule(AnnealingSchedule):
    """
    Annealing schedule via c/log(1+t).
    NOTE: *Very* slow to anneal.

    In a slightly different context, the condition on c is that it is greater
    than or equal to the depth of the greatest local minimum.
    See: Cooling Schedules for Optimal Annealing,
         Mathematics of Operations Research, 1988
    """
    def __init__(self, c):
        assert c >= 0
        self.c = c
        self.ticks = 0

    def next(self):
        self.ticks += 1
        return self.c / log(1.+self.ticks)
