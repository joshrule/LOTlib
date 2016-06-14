
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='WORLD-STATE')

# !! Note the types have changed since play1
grammar.add_rule('WORLD-STATE', '%s.stack()',           ['WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.left_grab(%s)',    ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.right_grab(%s)',    ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.left_drop()',    ['WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.right_drop()',    ['WORLD-STATE'], 1.0)

grammar.add_rule('WORLD-STATE',   'ws',    None, 10.0)
grammar.add_rule('WORLD-STATE', 'if_',    ['BOOL', 'WORLD-STATE', 'WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', 'recurse_',         ['WORLD-STATE'], 1.0)

grammar.add_rule('BOOL',   '(%s > %s)',              ['SIZE', 'SIZE'], 1.0)
grammar.add_rule('BOOL',   '(%s == %s)',              ['SIZE', 'SIZE'], 1.0)

grammar.add_rule('SIZE',   'getattr(%s,"top_size",None)',        ['OBJECT'], 1.0)
grammar.add_rule('SIZE',   'getattr(%s,"bottom_size",None)',     ['OBJECT'], 1.0)
grammar.add_rule('SIZE',   'getattr(%s,"height",None)',          ['OBJECT'], 1.0) # number of parts


grammar.add_rule('OBJECT', 'ws.choose_random()', None, 1.0)
# grammar.add_rule('OBJECT', '%s.choose_random()', ['WORLD-STATE'], 1.0)
grammar.add_rule('OBJECT', '%s.left_hand', ['WORLD-STATE'], 1.0)
grammar.add_rule('OBJECT', '%s.right_hand', ['WORLD-STATE'], 1.0)

# grammar.add_rule('SET', '%s.table', ['WORLD-STATE'], 5.0)
# grammar.add_rule('SET', 'diff_', ['SET', 'SET'], 1.0)
# grammar.add_rule('SET', 'set([%s])', ['OBJECT'], 1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WorldException(Exception):
    pass

class Cup(object):
    def __init__(self, top_size=0, bottom_size=1, height=1):
        self.__dict__.update(locals())

class WorldState(object):
    """
    Capture the world state. By default, everything should return a worldstate (self is okay)

    """

    def __init__(self):
        self.table =  set([Cup(top_size=n+1, bottom_size=n, height=1) for n in xrange(10)])
        self.left_hand  = None
        self.right_hand = None

    def __str__(self):
        return '[%s, %s, %s]'  % (self.left_hand, self.right_hand, str([x.height for x in self.table]))

    def left_grab(self, x):
        if x in self.table and x is not None:

            if self.left_hand is not None:
                self.left_drop()

            self.left_hand = x

            self.table.remove(x)
        else:
            raise WorldException

        return self


    def right_grab(self, x):
        if x in self.table and x is not None:

            if self.right_hand is not None:
                self.right_drop()

            self.right_hand = x

            self.table.remove(x)
        else:
            raise WorldException

        return self

    def left_drop(self):
        if self.left_hand is not None:
            self.table.add(self.left_hand)

        self.left_hand = None

        return self

    def right_drop(self):

        if self.right_hand is not None:
            self.table.add(self.right_hand)

        self.right_hand = None

        return self

    def stack(self):
        # Put right hand on top of the left

        x, y = self.left_hand, self.right_hand

        if x is not None and y is not None and (y.bottom_size <= x.top_size):  # can't put something on top of itself:
            c = Cup(top_size=y.top_size, bottom_size=x.bottom_size, height=x.height + y.height)

            self.left_hand = c
            self.right_hand = None
        else:
            raise WorldException

        return self

    def choose_random(self):
        if len(self.table) > 1:
            return sample1(self.table)
        else:
            raise WorldException



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib import break_ctrlc
from LOTlib.Miscellaneous import sample1, Infinity, q, attrmem
from LOTlib.Hypotheses.RecursiveLOTHypothesis import RecursiveLOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

class StackerHypothesis(RecursiveLOTHypothesis):

    def __init__(self, grammar=grammar, **kwargs):
        RecursiveLOTHypothesis.__init__(self, grammar=grammar, display='lambda recurse_, ws: %s', **kwargs) # for recursive hypotheses, must pass in recurses

    @attrmem('likelihood')
    def compute_likelihood(self, data, shortcut=None):
        assert len(data) == 0

        ws = WorldState()

        try:
            ws = self(ws)

        except (TooBigException, RecursionDepthException):
            return -100
        except WorldException:
            pass

        return max([x.height for x in list(ws.table)] + [getattr(ws.left_hand, "height", 0),
                                                         getattr(ws.right_hand, "height", 0)])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# for _ in xrange(1000):
#     h = StackerHypothesis()
#     # print q(h)
#     print h.compute_likelihood([]), q(h)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

# we'll run with a low likelihood_temperature to count the data more

for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.01)):
    print h.posterior_score, h.prior, h.likelihood, q(h)


