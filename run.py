
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='EXPR')

grammar.add_rule('EXPR', '(%s if %s else %s)', ['EXPR', 'BOOL', 'EXPR'], 4.0)
grammar.add_rule('EXPR', 'recurse_',           [],                       1.0)
grammar.add_rule('EXPR', 'cons_',              ['EXPR', 'EXPR'],         4.0)
grammar.add_rule('EXPR', '(%s)(%s)',           ['FUNC', 'EXPR'],         1.0)
grammar.add_rule('FUNC', 'lambda',             ['EXPR'],                 1.0, bv_type='EXPR', bv_p=4.0)
grammar.add_rule('EXPR', '"a"',                None,                     4.0)
grammar.add_rule('EXPR', '"b"',                None,                     4.0)
grammar.add_rule('EXPR', '"c"',                None,                     4.0)
grammar.add_rule('EXPR', '"d"',                None,                     4.0)

grammar.add_rule('BOOL', 'flip_',              [],                       1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from collections import Counter
from LOTlib.Miscellaneous import attrmem
from LOTlib.Hypotheses.RecursiveLOTHypothesis import RecursiveLOTHypothesis
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Hypotheses.Likelihoods.LevenshteinLikelihood import StochasticLevenshteinLikelihood

def list2str(lst):
    """Map a list (of lists) to a convenient string"""
    return '('+','.join([a if isinstance(a,str) else list2str(a) for a in lst])+')'

class StochasticTreeHypothesis(StochasticLevenshteinLikelihood, RecursiveLOTHypothesis):
    """
    A recursive LOT hypothesis that computes its (pseudo)likelihood using a string edit
    distance
    """

    def __init__(self, display="lambda recurse_: %s", **kwargs):
        RecursiveLOTHypothesis.__init__(self, grammar, display=display, recursive_depth_bound=5, **kwargs)

    def recursive_call(self, *args):
        """ Overwrite this to keep the depth shallow and return 'x' instead of an exception """
        self.recursive_call_depth += 1

        if self.recursive_call_depth > self.recursive_depth_bound:
            return 'x'

        # Call with sending myself as the recursive call
        return LOTHypothesis.__call__(self, self.recursive_call, *args)

    @attrmem('ll_counts')
    def make_ll_counts(self, input, nsamples=512):
        # Just a wrapper to make sure we use strings instead of the lists that are returned by __call__

        llcounts = Counter()
        for _ in xrange(nsamples):
            llcounts[list2str(self(*input))] += 1

        return llcounts

def make_hypothesis(**kwargs):
    return StochasticTreeHypothesis(**kwargs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Main code
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


if __name__ == "__main__":

    from Tree import draw_tree_grid


    from LOTlib.DataAndObjects import FunctionData
    data = [ FunctionData(input=(), output={ list2str(['a', 'b']):8,
                                             list2str(['a', [['a', 'b'], 'b']]):4,
                                             list2str(['a', [['a', [['a', 'b'], 'b']], 'b']]):2})  ]
    h0 = make_hypothesis()

    plot_every = 1000

    from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
    from LOTlib import break_ctrlc

    for i, h in enumerate(break_ctrlc(MHSampler(h0, data))):
        print h.posterior_score, h.prior, h.likelihood, h
        print h.ll_counts

        if i%plot_every == 0:
            draw_tree_grid('o.png', [h() for a_ in xrange(100)])
