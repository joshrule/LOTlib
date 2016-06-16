
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A Desired Program
#
# grab something in the left hand
# grab something in the right hand
# if you can stack them tightly, do that and drop them
# otherwise, drop them and recurse
#
# recurse_(
#   if(
#     get_bottom(
#       ws.left_grab(ws.choose_random())
#         .left_hand) ==
#     get_top(
#       ws.right_grab(ws.choose_random())
#         .right_hand),
#     ws.stack().left_drop(),
#     ws.left_drop().right_drop()))
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='WORLD-STATE')

grammar.add_rule('WORLD-STATE', '%s.stack()',                     ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.left_grab(%s)',               ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.right_grab(%s)',              ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.left_drop()',                 ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.right_drop()',                ['WORLD-STATE'],           1.0)

grammar.add_rule('WORLD-STATE', 'ws',                             None,                      10.0)
grammar.add_rule('WORLD-STATE', 'if_',                            ['BOOL', 'WORLD-STATE', 'WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', 'recurse_',                       ['WORLD-STATE'],           1.0)

grammar.add_rule('OBJECT',      '%s.choose_random()',             ['WORLD-STATE'],           1.0)
grammar.add_rule('OBJECT',      '%s.left_hand',                   ['WORLD-STATE'],           1.0)
grammar.add_rule('OBJECT',      '%s.right_hand',                  ['WORLD-STATE'],           1.0)

grammar.add_rule('SIZE',        'getattr(%s,"height",None)',      ['OBJECT'],                1.0) # number of cups in stack
grammar.add_rule('SIZE',        'getattr(%s,"top_size",None)',    ['OBJECT'],                1.0)
grammar.add_rule('SIZE',        'getattr(%s,"bottom_size",None)', ['OBJECT'],                1.0)

grammar.add_rule('BOOL',        '(%s > %s)',                      ['SIZE', 'SIZE'],          1.0)
grammar.add_rule('BOOL',        '(%s == %s)',                     ['SIZE', 'SIZE'],          1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Data Structures
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Stack(object):
    """Stacks have a top size, bottom size, and height"""
    def __init__(self, top_size=0, bottom_size=1, height=1):
        self.__dict__.update(locals())

class WorldException(Exception):
    pass

class WorldState(object):
    """
    Capture the world state. By default, everything should return a worldstate (self is okay)

    """

    def __init__(self):
        self.table =  set([Stack(top_size=n, bottom_size=n+1, height=1) for n in xrange(10)])
        self.left_hand  = None
        self.right_hand = None

    def __str__(self):
        return '[%s, %s, %s]'  % (self.left_hand, self.right_hand, str([x.height for x in self.table]))

    def left_grab(self, x):
        if x in self.table and x is not None and self.left_hand is None:
            self.left_hand = x
            self.table.remove(x)
        else:
            raise WorldException
        return self

    def right_grab(self, x):
        if x in self.table and x is not None and self.right_hand is None:
            self.right_hand = x
            self.table.remove(x)
        else:
            raise WorldException
        return self

    def left_drop(self):
        if self.left_hand is not None:
            self.table.add(self.left_hand)
            self.left_hand = None
        else:
            raise WorldException
        return self

    def right_drop(self):
        if self.right_hand is not None:
            self.table.add(self.right_hand)
            self.right_hand = None
        else:
            raise WorldException
        return self

    def stack(self):
        """ Put right hand on top of the left """
        l, r = self.left_hand, self.right_hand

        if type(l) is not Stack or type(r) is not Stack or (r.bottom_size > l.top_size):  # can't put something on top of itself:
            raise WorldException
        else:
            c = Stack(top_size=r.top_size, bottom_size=l.bottom_size, height=l.height + r.height)
            self.left_hand = c
            self.right_hand = None

        return self

    def choose_random(self):
        if len(self.table) >= 1:
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
            return -Infinity
        except WorldException:
            pass

        return (max([x.height for x in list(ws.table)] + [getattr(ws.left_hand, "height", 0),
                                                         getattr(ws.right_hand, "height", 0)])) # -
#                log(float(self.recursive_call_depth+1)))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

# we use a low likelihood_temperature to favor higher likelihoods and count the data more
for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.01)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
