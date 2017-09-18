"""
Metropolis-Hastings with parallel tempering for the chain
"""
import random
import LOTlib.Miscellaneous as misc
import LOTlib.Inference.Samplers.Sampler as S
import LOTlib.Inference.Samplers.MultipleChainMCMC as MCMCMC


class ParallelTemperedMHSampler(MCMCMC.MultipleChainMCMC):
    """
    A Metropolis-Hastings sampler with parallel tempering for the chain.

    Notes
    -----
    - This includes stats on up-vs-down for tuning the temperatures.

    Parameters
    ----------
    h0 : LOTlib.Hypotheses.Hypothesis
        the initial hypothesis
    data : list of data
        the data from which to learn
    steps : int, optional
        how many total samples to collect across all chains (default: Infinity)
    what : {'chain', 'hypothesis'}
        which are we tempering, the chain or the hypothesis?
    temperatures : list of floats, optional
        which temperatures to use, specifies the number of chains
        (default: [1.0, 1.05, 1.15, 1.2])
    within_steps : int
        how many samples to collect from each chain between XX (default: 100)
    swaps : int
        how many swaps to propose after each `within_steps` samples
    yield_only_t0 : bool
        return only samples from the lowest temperature chain? (default: False)
    print_swapstats : bool
        print swapping statistics for tuning the temperatures? (default: False)
    **kwargs :
        additional args for the underlying MHSampler
    """

    def __init__(self, h0, data, steps=misc.Infinity, what='chain',
                 temperatures=[.1, 1.05, 1.15, 1.2], within_steps=100, swaps=2,
                 yield_only_t0=False, print_swapstats=False, **kwargs):

        self.what = what
        self.within_steps = within_steps
        self.swaps = swaps
        self.yield_only_t0 = yield_only_t0
        self.print_swapstats = print_swapstats

        if 'nchains' in kwargs:
            raise ValueError('ParallelTemperedMHSampler: cannot accept ' +
                             '\'nchains\' argument')

        super(ParallelTemperedMHSampler, self).__init__(
            h0, data, nchains=len(temperatures), steps=steps, **kwargs)

        self.temperatures = temperatures

        # set the temperatures
        for c, t in zip(self.chains, temperatures):
            if self.what == 'hypothesis':
                c.current_sample.temperature = t
            else:
                c.temperature = t

        # Keep track of the number of swaps
        # how often are you swapped with the immediately higher chain
        self.upswaps = [0] * (self.nchains-1)

        # Keep track of up and down from each chain
        for t in self.chains:
            # +1 for up, -1 for down
            t.updown = 0
        self.chains[0].updown = 1
        self.chains[len(temperatures)-1].updown = -1

        # fraction of particles that are up and down
        self.nup = [0] * self.nchains
        self.ndown = [0] * self.nchains

    def get_hist(self, smoothed=0.001):
        """
        Return a mildly smoothed histogram

        Returns
        -------
        list of ints
            smoothed ratios of promotions to total movement for each chain.
        """
        return [float(a+smoothed)/(float(a+b+2*smoothed))
                for a, b in zip(self.nup, self.ndown)]

    def propose_swaps(self):
        """proposes & accepts/rejects `self.swaps` swaps between chains"""
        for _ in xrange(self.swaps):

            # select one of the first n-1 chains
            i = random.randint(0, self.nchains-2)

            # compute the necessary probabilities
            cur = (self.chains[i].current_sample.posterior_score +
                   self.chains[i+1].current_sample.posterior_score)
            if self.what == 'hypothesis':
                self.chains[i+1].current_sample.temperature = \
                    self.temperatures[i]
                self.chains[i].current_sample.temperature = \
                    self.temperatures[i+1]
                prop = (self.chains[i].current_sample.posterior_score +
                        self.chains[i+1].current_sample.posterior_score)
                self.chains[i].current_sample.temperature = \
                    self.temperatures[i]
                self.chains[i+1].current_sample.temperature = \
                    self.temperatures[i+1]
            else:
                prop = (self.chains[i].at_temperature(self.temperatures[i+1]) +
                        self.chains[i+1].at_temperature(self.temperatures[i]))

            # print stats as desired
            if self.print_swapstats:
                print "# Proposing ", cur-prop, self.upswaps, self.get_hist()

            # swap if accepted
            if S.MH_acceptance(cur, prop, 0.0):
                # update the counts
                for idx in [i, i+1]:
                    self.nup[idx] += (self.chains[idx].updown == 1)
                    self.ndown[idx] += (self.chains[idx].updown == -1)

                # TODO: Why move the entire chain rather than the hypotheses?
                tmp = self.chains[i]
                self.chains[i] = self.chains[i+1]
                self.chains[i+1] = tmp

                if self.what == 'hypothesis':
                    self.chains[i].current_sample.temperature = \
                        self.temperatures[i+1]
                    self.chains[i+1].current_sample.temperature = \
                        self.temperatures[i]
                else:
                    self.chains[i].temperature = self.temperatures[i+1]
                    self.chains[i+1].temperature = self.temperatures[i]

                self.upswaps[i] += 1

                # keep track of who is up and down
                # TODO: is this right? Shouldn't we reset the previous updowns?
                if i == 0:
                    self.chains[i].updown = 1
                elif i == self.nchains-2:
                    self.chains[self.nchains-1].updown = -1

    def next(self):
        """
        Generate another sample.

        Returns
        -------
        LOTlib.Hypotheses.Hypothesis
            the current sample (a new one if accepted else the old one)
        """
        # increase the number of samples
        self.nsamples += 1

        # move to the next chain
        self.chain_idx = (self.chain_idx+1) % self.nchains

        # propose swaps if you've sampled `within_steps` samples
        if self.nsamples % self.within_steps == 0:
            self.propose_swaps()

        # manage yield from all chains or just lowest temp. chain
        if self.yield_only_t0 and self.chain_idx != 0:
            # TODO: FIX. IT BREAKS WITH TOO MANY CHAINS (recursion depth)
            # TODO: DON'T WE NEED TO ADVANCE THE OTHER CHAINS?
            # keep going until we're on the one we yield
            return self.next()
        return self.chains[self.chain_idx].next()
