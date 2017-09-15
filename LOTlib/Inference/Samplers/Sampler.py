from LOTlib.Miscellaneous import Infinity


from math import log, exp, isnan
from random import random


def MH_acceptance(cur, prop, fb, p=None, temperature=1.0):
    """
    decides whether to accept a proposal while handling corner cases

    Corner case handling is motivated by computing MH acceptance ratios.

    Parameters
    ----------
    cur : float
        The current sample's posterior score
    prop : float
        The proposal's posterior score
    fb : float
        The forward-backward ratio
    p : float or None, optional
        If a float is specified, this is the random sample drawn
    temperature : float, optional
        What is the temperature of this acceptance?
    Returns
    -------
    bool
        True if we accept and False if we reject
    """
    # If we get infs or are in a stupid state, just sample from the prior
    if isnan(cur) or (cur == -Infinity and prop == -Infinity):
        # choose at random -- don't sample priors since they may both be -inf
        r = -log(2.0)

    elif isnan(prop) or prop == -Infinity or fb == Infinity:
        # never accept
        return False

    else:
        r = (prop-cur-fb) / temperature

    # And flip unless we supplied the p
    return r >= 0.0 or ((p if p is not None else random()) < exp(r))


class Sampler(object):
    """
    Sampler class template in generator format

    - call __iter__() or next() to yield more samples.
    - 'States' for the sampler refer to the most recently yielded sample.
    """

    def __init__(self):
        raise NotImplementedError

    def __iter__(self):
        return self

    def next(self):
        raise NotImplementedError

    def get_state(self):
        return self.current_sample

    def set_state(self, s, compute_posterior=True):
        """Set the current sample, maybe compute its posterior.

        Args
        ----
        s : Hypothesis
            Set `self.current_sample` to this.
        compute_posterior : bool
            If true, compute its posterior.

        """
        self.current_sample = s
        if compute_posterior:
            self.current_sample.compute_posterior(self.data)

    def str(self):
        return "<%s sampler in state %s>" % (type(self), self.current_sample)

    def take(self, n, **kwargs):
        """
        Yield the next `n` samples.

        """
        for _ in xrange(n):
            yield self.next(**kwargs)

    def compute_posterior(self, h, data, shortcut=-Infinity):
        """
        A wrapper for hypothesis.compute_posterior(data).
        It can be overwritten in fancy subclassses.
        """
        self.posterior_calls += 1
        return h.compute_posterior(data, shortcut=shortcut)
