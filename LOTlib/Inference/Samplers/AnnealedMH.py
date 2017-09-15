"""
Metropolis-Hastings with simulated annealing
"""
import LOTlib.Inference.Samplers.AnnealingSchedule as AS
import LOTlib.Inference.Samplers.MetropolisHastings as MH


class AnnealedMHSampler(MH.MHSampler):
    """
    A Metropolis-Hasting sampler with simulated annealing.

    Simulated annealing works here by adjusting the temperature of either the
    chain itself or the temperature of the hypothesis according to a schedule.

    Parameters
    ----------
    h0 : LOTlib.Hypotheses.Hypothesis
        the initial hypothesis
    data : list of data
        the data from which to learn
    what : {'chain', 'hypothesis'}
        what is being annealed, the chain or the hypothesis
    schedule : LOTlib.Inference.Samplers.AnnealingSchedule, optional
        the schedule according to which the temperature is annealed
        (default: constant schedule of 1.0)
    **kwargs :
        additional args for the underlying MHSampler
    """

    def __init__(self, h0, data, what='chain', schedule=None, **kwargs):
        self.what = what
        if schedule is not None:
            self.schedule = schedule
        else:
            self.schedule = AS.ConstantSchedule(1.0)
        super(AnnealedMHSampler, self).__init__(h0, data, **kwargs)

    def next(self):
        """
        generate a new sample

        Returns
        -------
        LOTlib.Hypotheses.Hypothesis
            the current sample (a new one if accepted else the old one)
        """
        # update the temperature according to the schedule
        if self.what == 'hypothesis':
            self.current_sample.temperature = self.schedule.next()
        else:
            self.temperature = self.schedule.next()
        # and generate a new sample
        return MH.MHSampler.next(self)
