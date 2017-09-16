"""
Multiple parallel MCMC chains running at once.
"""
from copy import copy
from LOTlib.Miscellaneous import Infinity
from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
from LOTlib.Inference.Samplers.Sampler import Sampler


class MultipleChainMCMC(Sampler):
    """
    Multiple parallel MCMC chains running at once.

    Run skip steps within each chain, looping to return samples in a roundrobin
    fashion, chain1, chain2, chain3, ...

    This is subclassed by several other inference techniques

    Parameters
    ----------
    h0 : LOTlib.Hypotheses.Hypothesis
        the initial hypothesis, used in each chain
    data : list of data
        what data we use
    steps : int
        how many *total* steps the sampler takes, not the number for each chain
    nchains : int
        how many chains
    **kwargs :
        special args to sampler
    """

    def __init__(self, h0, data, steps=Infinity, nchains=10, **kwargs):

        self.nchains = nchains
        # what chain are we on?
        # This get incremented before anything, so it starts with 0
        self.chain_idx = -1
        self.nsamples = 0
        if nchains <= 0:
            raise ValueError('MultipleChainMCMC: must have > 0 chains' +
                             '(you sent %s)'.format(nchains))

        self.chains = [self.make_sampler(h0,
                                         data,
                                         steps=steps/nchains,
                                         **kwargs)
                       for _ in xrange(nchains)]

    def make_sampler(self, h0, data, **kwargs):
        """
        make each an internal sampler.

        It can be overwritten if you want something fnacy

        Parameters
        ----------
        h0 : LOTlib.Hypotheses.Hypothesis
            the initial hypothesis, used in each chain
        data : list of data
            what data we use
        **kwargs :
            special args to sampler

        Returns
        -------
        LOTlib.Inference.Samplers.Sampler
            a sampler to be used in one of the chains
        """
        return MHSampler(h0, data, **kwargs)

    def __iter__(self):
        return self

    def next(self):
        self.nsamples += 1
        self.chain_idx = (self.chain_idx+1) % self.nchains
        return self.chains[self.chain_idx].next()

    def reset_counters(self):
        for c in self.chains:
            c.reset_counters()

    def acceptance_ratio(self):
        """
        Return the acceptance rate of all chains

        Returns
        -------
        list of floats
            the acceptance rates of the chains
        """
        return [c.acceptance_ratio() for c in self.chains]

    def set_state(self, s, **kwargs):
        """
        Set the state of each chain in  sampler.

        By necessity, we set the states of all samplers to copies. This is
        required when, for instance, we parallel temper within PartitionMCMC.

        Parameters
        ----------
        s : hypothesis
            the state to which we set all the chains
        **kwargs :
            any additional arguments we want to pass to the chains' set_state
        """
        for c in self.chains:
            # copy s first, or all hell breaks loose
            c.set_state(copy(s), **kwargs)
