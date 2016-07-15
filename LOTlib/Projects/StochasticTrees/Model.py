
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
    """Map a list (of lists) to a convenient string - no quote marks!"""
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

    from DrawTree import draw_tree_grid
    from LOTlib import break_ctrlc,SIG_INTERRUPTED
    from LOTlib.DataAndObjects import FunctionData
    from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
    from LOTlib.Inference.Samplers.StandardSample import standard_sample
    from LOTlib.MPI.MPI_map import MPI_unorderedmap, is_master_process
    import itertools
    import numpy

    def run(make_hypothesis, make_data):
        """
        This out on the DATA_RANGE amounts of data and returns all hypotheses in top count
        """
        if SIG_INTERRUPTED:
            return set()

        topCount = 100
        steps = 10000
        return standard_sample(make_hypothesis,
                               make_data,
                               N=topCount,
                               steps=steps,
                               show=False,save_top=None)

        # plot_every = 1000
        # if i%plot_every == 0:
        #      draw_tree_grid('o.png', [h() for a_ in xrange(100)])

    # part concept 2: SUCCESS (with lambdas)!
    # lambda recurse_: cons_(cons_("b", cons_("b", (cons_("d", "b") if flip_() else cons_("d", "b")))), cons_("c", cons_("b", cons_("d", "b"))))
    data = [ FunctionData(input=(), output={ list2str( [['b', [['b', 'a'], ['d', 'b']]], ['c', [['b', 'a'], ['d', 'b']]]] ):16 })]
    def make_data():
        return data
 
    # choose the appropriate map function
    nChains = 6
    args = list(itertools.product([make_hypothesis],[make_data] * nChains) )

    seen = set()
    for fs in MPI_unorderedmap(run, numpy.random.permutation(args)):
        assert is_master_process()
        print "another one bites the dust!"

        for h in fs:

            if h not in seen:
                seen.add(h)

#               if eval_data is not None:
#                   h.compute_posterior(eval_data) # evaluate on the big data
#                   print h.posterior_score, h.prior, h.likelihood / options.EVAL_DATA, \
#                           alsoprint(h) if alsoprint is not None else '',\
#                           qq(cleanFunctionNodeString(h))

    import pickle
    with open('/home/rule/projects/stochastic_trees/test.pkl', 'w') as f:
        pickle.dump(seen, f)

# OTHER DATA

#    # prototype concept: SUCCESS  (with lambdas)!
#    data = [ FunctionData(input=(), output={ list2str(['a', ['a', [['b', 'c'], 'c']]]):16 })]
    
#    # nested prototype concept 0: SUCCESS (with lambdas)!
#    # lambda recurse_: cons_("a", cons_("b", ("c" if flip_() else "d")))
#    data = [ FunctionData(input=(), output={ list2str(['a', ['b', 'c']]):8,
#                                             list2str(['a', ['b', 'd']]):8 })]

#    # nested prototype concept 1: SUCCESS (with lambdas)!
#    # lambda recurse_: cons_("a", cons_("b", (cons_("d", "c") if flip_() else "c")))
#    data = [ FunctionData(input=(), output={ list2str(['a', ['b', 'c']]):8,
#                                             list2str(['a', ['b', ['d', 'c']]]):8 })]

#    # nested prototype concept 2: FAILURE
#    # The problem is that it can't figure out that it should flip
#    # between (cons a c) and (cons d b). Instead, it conses two flips.
#    # This has happened in 5-6 chains that I've run.
#    data = [ FunctionData(input=(), output={ list2str(['a', ['b', ['a', 'c']]]):8,
#                                             list2str(['a', ['b', ['d', 'b']]]):8 })]
    
#    # CogSci nested prototype concept:
#    # sampe problem as nested prototype 2
#    data = [ FunctionData(input=(), output={ list2str(['a', ['b', ['a', [['c', [['a', ['a', 'b']], 'b']], 'a']]]]):8,
#                                             list2str(['a', ['b', ['a', [[['b', 'a'],['c','c']],'c']]]]):8 })]

#    # part concept 0: SUCCESS (with lambdas)!
#    # lambda recurse_: cons_(cons_("b", cons_("b", "b")), cons_("c", cons_("b", "b")))
#    data = [ FunctionData(input=(), output={ list2str( [['b', ['b', 'b']], ['c', ['b', 'b']]] ):16 })]

#    # part concept 1: SUCCESS (with lambdas)!
#    # lambda recurse_: cons_(cons_("b", cons_("b", (cons_("d", "b") if flip_() else cons_("d", "b")))), cons_("c", cons_("b", cons_("d", "b"))))
#    data = [ FunctionData(input=(), output={ list2str( [['b', ['b', ['d', 'b']]], ['c', ['b', ['d', 'b']]]] ):16 })]

    # CogSci part concept
#    data = [ FunctionData(input=(), output={ list2str( [[['b', ['a', ['b', 'b']]], ['c', ['a', ['b', 'b']]]],['d', ['a', ['b', 'b']]]] ):16 })]

#    # parameterized part concept
#    data = [ FunctionData(input=(), output={ list2str([[['a', 'b'], [[['a', 'b'], [[['a', 'b'], [['a', 'b'], 'b']], 'b']], 'b']], 'b']):8,
#                                             list2str([[['a', 'c'], [[['a', 'c'], [[['a', 'c'], [['a', 'c'], 'c']], 'c']], 'c']], 'c']):8 })]
             
#    # Steve's single recursion concept: SUCCESS (without lambdas)!
#    branch: ['a', [??, 'b']]
#    leaf: ['a', 'b']
#    data = [ FunctionData(input=(), output={ list2str(['a', 'b']):8,
#                                             list2str(['a', [['a', 'b'], 'b']]):4,
#                                             list2str(['a', [['a', [['a', 'b'], 'b']], 'b']]):2 })]

#    # single recursion concept:
#    base: ['c', [['a', ??], 'b']]
#    branch1: [['a', [['a', 'b'] 'b']], ??]
#    branch2: ['c', 'd']
#    data = [ FunctionData(input=(), output={ list2str([['a', [['a', 'b'] 'b']], ['c', 'd']]):8,
#                                             list2str([['a', [['a', 'b'] 'b']], ['c', [['a', ['c', 'd']], 'b']]]):4,
#                                             list2str([['a', [['a', 'b'] 'b']], ['c', [['a', ['c', [['a', ['c', 'd']], 'b']]], 'b']]]):2,
#                                             list2str([['a', [['a', 'b'] 'b']], ['c', [['a', ['c', [['a', ['c', [['a', ['c', 'd']], 'b']]], 'b']]], 'b']]]):1 })]


#    # multiple recursion concept
#    base: [['a', ['b' ['c', ?]]], ?]
#    branch1: ['d',  ? ]
#    branch2: ['d', 'b']
#    branch3: ['d', 'd']
#    data = [ FunctionData(input=(), output={ list2str([['a', ['b' ['c', ['d', 'd']]]], ['d', 'd']]):4
#                                             list2str([['a', ['b' ['c', ['d', 'd']]]], ['d', 'b']]):4
#                                             list2str([['a', ['b' ['c', ['d', 'b']]]], ['d', 'd']]):4
#                                             list2str([['a', ['b' ['c', ['d', 'b']]]], ['d', 'b']]):4
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'd']]]]], ['d', 'd']]):2
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'd']]]]], ['d', 'b']]):2
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'b']]]]], ['d', 'd']]):2
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'b']]]]], ['d', 'b']]):2
#                                             list2str([['a', ['b' ['c', ['d', 'd']]]], ['d', ['d', 'd']]]):2
#                                             list2str([['a', ['b' ['c', ['d', 'd']]]], ['d', ['d', 'b']]]):2
#                                             list2str([['a', ['b' ['c', ['d', 'b']]]], ['d', ['d', 'd']]]):2
#                                             list2str([['a', ['b' ['c', ['d', 'b']]]], ['d', ['d', 'b']]]):2
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'd']]]]], ['d', ['d', 'd']]]):1
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'd']]]]], ['d', ['d', 'b']]]):1
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'b']]]]], ['d', ['d', 'd']]]):1
#                                             list2str([['a', ['b' ['c', ['d', ['d', 'b']]]]], ['d', ['d', 'b']]]):1 })]
