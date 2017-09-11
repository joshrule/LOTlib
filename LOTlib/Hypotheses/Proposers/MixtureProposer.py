from itertools import izip
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


def give_proposal_log_p_maker(proposal_fns, weights):
    def give_proposal_log_p(old, new, **kwargs):
        """prob. of generating new from old, adjusted for weight"""
        ps = []
        for p, w in izip(proposal_fns, weights):
            log_p = p[1](old, new, **kwargs)
            ps += [log_p + log(w)]
            # print p[1].__name__, '->', log_p
        return logsumexp(ps)
        # return logsumexp([p[1](old, new, **kwargs) + log(w)
        #                   for p, w in izip(proposal_fns, weights)])
    return give_proposal_log_p


class MixtureProposer(Proposer):
    """
            A mixture proposal (ONLY ERGODIC IF MIXTURE IS ERGODIC!)

    Given a weighted list of proposal methods, create a proposal using
            these as subproposals in proportion to their weight.
            """
    def __init__(self, proposal_fns=[], weights=[], **kwargs):
        """
        Create a MixtureProposer

        Args:
          proposal_fns: a list of N (propose_value, give_proposal_log_p) pairs
          weights: a list of N floats, the weights of the proposers
        """
        if len(proposal_fns) != len(weights):
            raise ValueError('MixtureProposer: weights don\'t match proposers')

        self.propose_value = propose_value_maker(proposal_fns, weights)
        self.give_proposal_log_p = give_proposal_log_p_maker(proposal_fns,
                                                             weights)
        super(MixtureProposer, self).__init__(**kwargs)
