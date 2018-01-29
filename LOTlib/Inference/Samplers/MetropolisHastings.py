from LOTlib.Miscellaneous import Infinity, self_update
from LOTlib.Inference.Samplers.Sampler import Sampler, MH_acceptance


class MHSampler(Sampler):
    """
    A class to implement MH sampling.

    You can create a sampler object::
        from LOTlib.Examples.Number.Shared import (generate_data,
                                                   NumberExpression,
                                                   grammar)
        data = generate_data(500)
        h0 = NumberExpression(grammar)
        sampler = MHSampler(h0, data, 10000)
        for h in sampler:
            print sampler.acceptance_ratio(), h

    Or implicitly::
        from LOTlib.Examples.Number.Shared import (generate_data,
                                                   NumberExpression,
                                                   grammar)
        data = generate_data(500)
        h0 = NumberExpression(grammar)
        for h in  MHSampler(h0, data, 10000):
            print h

    Parameters
    ----------
    current_sample : doc?
        if None, don't compute its posterior (via set_state), else do.
    data : doc?
        doc?
    steps : int
        Number of steps to generate before stopping.
    proposer : function
        Defaultly this calls the sample Hypothesis's propose() function.
        If specified, `proposer` must return a *new copy* of the object.
    skip : int
        Throw out this many samples each time MHSampler yields a sample.
    temperature : float
        The temperature of the sampler (modifies acceptance probabilities).
    trace : bool
        If true, print stuff as we sample.
    shortcut_likelihood : bool
        If true, use short-cut evaluation of the likelihood, rejecting if
        the ll drops below the acceptance value.

    Attributes
    ----------
    was_accepted : bool
        Was the last proposal accepted?
    samples_yielded : int
        How many samples have I yielded? This doesn't count skipped samples.
    """

    def __init__(self, current_sample, data, steps=Infinity, proposer=None,
                 skip=0, temperature=1., trace=False, shortcut_likelihood=True):
        self_update(self, locals())

        if proposer is None:
            self.proposer = lambda x: x.propose()

        self.set_state(current_sample,
                       compute_posterior=(current_sample is not None))

        self.was_accepted = None
        self.samples_yielded = 0
        self.reset_counters()

    def at_temperature(self, t):
        """
        compute posterior probability at a given temperature

        Args
        ----
        t : float
            Set temperature to this value.
        Returns
        -------
        float
            the posterior probability at temperature `t`
        """
        return (self.current_sample.prior + self.current_sample.likelihood)/t

    def reset_counters(self):
        """
        Reset acceptance and proposal counters.
        """
        self.acceptance_count = 0
        self.proposal_count = 0
        self.posterior_calls = 0

    def acceptance_ratio(self):
        """
        Returns the proportion of proposals that have been accepted.

        Returns
        -------
        float
            the proportion of proposals that have been accepted
        """
        if self.proposal_count > 0:
            return float(self.acceptance_count) / float(self.proposal_count)
        else:
            return float("nan")

    def next(self):
        """
        Generate another sample.

        Returns
        -------
        LOTlib.Hypotheses.Hypothesis
            the current sample (a new one if accepted else the old one)
        """
        if self.samples_yielded >= self.steps:
            raise StopIteration
        else:
            for _ in xrange(self.skip+1):

                self.proposal, fb = self.proposer(self.current_sample)

                if self.proposal is self.current_sample or \
                   self.proposal.value is self.current_sample.value:
                    raise ValueError('MetropolisHastings.next: proposal ' +
                                     'is the same as the current sample!')

                # Call myself so memoized subclasses can override
                self.compute_posterior(self.proposal, self.data)

                prop = self.proposal.posterior_score
                cur = self.current_sample.posterior_score

                if self.trace:
                    print "# FB: ", round(fb, 3)
                    print "# Current: ", round(cur, 3),
                    print str(self.current_sample).replace('\n', '\n# ')
                    print "# Proposal:", round(prop, 3),
                    print str(self.proposal).replace('\n', '\n# ')
                    print

                if MH_acceptance(cur, prop, fb, temperature=self.temperature):
                    self.current_sample = self.proposal
                    self.was_accepted = True
                    self.acceptance_count += 1
                else:
                    self.was_accepted = False

                self.proposal_count += 1

            self.samples_yielded += 1
            return self.current_sample


if __name__ == "__main__":
    # an example

    from LOTlib import break_ctrlc
    from LOTlib.Examples.Number.Model import (make_data,
                                              NumberExpression,
                                              grammar)

    data = make_data(300)
    h0 = NumberExpression(grammar)
    sampler = MHSampler(h0, data, steps=100000)
    for h in break_ctrlc(sampler):
        print \
            h.posterior_score, \
            h.prior, \
            h.likelihood, \
            h.compute_likelihood(data), \
            h
