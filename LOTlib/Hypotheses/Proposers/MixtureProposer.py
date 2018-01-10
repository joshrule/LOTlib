import itertools as itools
from scipy.misc import logsumexp
from numpy.random import choice
from numpy import log

from LOTlib.Hypotheses.Proposers.Proposer import Proposer


def propose_value_maker(proposal_fns, weights):
    def propose_value(value, **kwargs):
        """sample a sub-proposer and propose from it"""
        p = proposal_fns[choice(len(proposal_fns), p=weights)][0]
        return p(value, **kwargs)
    return propose_value


def give_proposal_log_fb_maker(proposal_fns, weights):
    def give_proposal_log_fb(old, new, **kwargs):
        """forward-backward probability, adjusted for weight"""
        fs = []
        bs = []
        for p, w in itools.izip(proposal_fns, weights):
            f, b = p[1](old, new, **kwargs)
            fs.append(f + log(w))
            bs.append(b + log(w))
            print p[1].__name__, '->', (f, b)
        return logsumexp(fs) - logsumexp(bs)
    return give_proposal_log_fb


class MixtureProposer(Proposer):
    """
    A mixture proposal (ONLY ERGODIC IF MIXTURE IS ERGODIC!)

    Given a weighted list of proposal methods, create a proposal using them as
    subproposals in proportion to their weight.

    Args:
      proposal_fns: a list of N (propose_value, give_proposal_log_p) pairs
      weights: a list of N floats, the weights of the proposers
    """
    def __init__(self, proposal_fns=[], weights=[], **kwargs):
        if len(proposal_fns) != len(weights):
            raise ValueError('MixtureProposer: weights don\'t match proposers')

        self.propose_value = propose_value_maker(proposal_fns, weights)
        self.give_proposal_log_fb = give_proposal_log_fb_maker(proposal_fns,
                                                               weights)
        super(MixtureProposer, self).__init__(**kwargs)
