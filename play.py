
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='ACTION')

grammar.add_rule('ACTION', 'stack_',           ['OBJECT', 'OBJECT'], 1.0)
grammar.add_rule('ACTION', 'if_',              ['BOOL', 'ACTION', 'ACTION'], 1.0)
grammar.add_rule('ACTION', 'noop_',            [], 1.0)
# grammar.add_rule('OBJECT', 'choose_random_',   ['SET'], 1.0)

grammar.add_rule('BOOL',   '(%s > %s)',              ['SIZE', 'SIZE'], 1.0)
grammar.add_rule('BOOL',   '(%s == %s)',              ['SIZE', 'SIZE'], 1.0)

grammar.add_rule('SIZE',   '%s.top_size',        ['OBJECT'], 1.0)
grammar.add_rule('SIZE',   '%s.bottom_size',     ['OBJECT'], 1.0)
grammar.add_rule('SIZE',   '%s.height',          ['OBJECT'], 1.0) # number of parts

grammar.add_rule('OBJECT', 'x', None, 1.0)
grammar.add_rule('OBJECT', 'y', None, 1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cup(object):
    def __init__(self, top_size=0, bottom_size=1, height=1):
        self.__dict__.update(locals())

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Primitives
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Eval import primitive

@primitive
def stack_(x,y): # put y on top of x
    if (x is not y) and (y.bottom_size <= x.top_size): # can't put something on top of itself:
        return Cup(top_size=y.top_size, bottom_size=x.bottom_size, height=x.height + y.height)
    else:
        return None

@primitive
def noop_():
    return None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib import break_ctrlc
from LOTlib.Miscellaneous import sample1, Infinity, q, attrmem
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Eval import TooBigException

class StackerHypothesis(LOTHypothesis):

    def __init__(self, grammar=grammar, **kwargs):
        LOTHypothesis.__init__(self, grammar=grammar, display='lambda x, y: %s', **kwargs)

    @attrmem('likelihood')
    def compute_likelihood(self, data, shortcut=None):
        assert len(data) == 0

        ll = 0

        NRUNS = 100
        MAX_IT = 1000

        # Average over a bunch of runs
        for _ in xrange(NRUNS):

            S = [Cup(top_size=n+1, bottom_size=n, height=1) for n in xrange(10)]
            it = 0

            while len(S) > 1:
                x, y = sample1(S), sample1(S)

                # call our function
                try:
                    r = self(x,y)
                except TooBigException:
                    r = None

                if r is not None:

                    S.remove(x) # remove from S
                    if y in S: # because it might be removed
                        S.remove(y)

                    S = S + [r]

                if it >  MAX_IT:
                    ll += max([x.height for x in S]) - log(MAX_IT)
                    break

                it += 1

            ll += S[0].height - log(it)

        return ll

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# for _ in xrange(100):
#     h = StackerHypothesis()
#
#     print h.compute_likelihood([]), q(h)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100)):
    print h.posterior_score, h.prior, h.likelihood, q(h)