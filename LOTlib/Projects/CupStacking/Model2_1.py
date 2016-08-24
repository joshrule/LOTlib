# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Model 2_1:
#
# This model is about as simple as a stacking model could get. We're
# not even interested in being able to express the various stages
# through which kids might be able to go, just the first one. This
# model looks at a very simple description of stacking one object on
# top of another.
#
# 1. given the current world state, choose two items
# 2. pick up the smaller item
# 2. stack the item in your hand on the other item
#
# This approach still doesn't seem to make it complicated enough to
# stack two items on top of each other. I can make the task harder by
# adding more intervening steps, such as choosing one cup, choosing
# the other, picking up the second cup, and then stacking it on the
# first.
#
# But, something seems missing here - a good explanation for why the
# initial pattern is firmly stuck at 2. It could just be a complicated
# motor pattern that needs to be learned, but there may be more to it
# than that. What could it be? I think we want to say that the program
# is hard enough to learn that you can't easily repeat the process. It
# seems too easy in the current language to repeat the stacking
# operation. How do we make that more difficult? It should require all
# the steps. Stacking should nullify the previous selections.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                 None,      10.0)
grammar.add_rule('STATE', '%s.choose_items()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.pick_smaller()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack()',        ['STATE'], 1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cup
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Miscellaneous import self_update

class Cup(object):
    """cups have a size"""
    def __init__(self, size=1):
        self_update(self,locals())

    def __repr__(self):
        return 'Cup(size=%s)' % self.size

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stack
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Stack(object):
    def __init__(self, parts=[]):
        self.parts = parts
        self.height = sum([1 if isinstance(part,Cup) else part.height for part in parts])
        if len(self.parts) > 0:
            self.top = self.parts[-1] if isinstance(self.parts[-1],Cup) else self.parts[-1].top
            self.bottom = self.parts[0] if isinstance(self.parts[0],Cup) else self.parts[0].bottom

    def __repr__(self):
        return 'Stack(parts=[%s])' % str([str(part) for part in self.parts])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# WorldState
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class WorldException(Exception):
    pass

from LOTlib.Miscellaneous import sample1
from copy import copy

class WorldState(object):
    """Capture the world state. Most functions should return worldstates."""
    def __init__(self):
        self.table =  { Stack([Cup(n)]) for n in xrange(10) }
        self.attention1 = None
        self.attention2 = None

    def __str__(self):
        return '[%s, %s, %s]'  % (self.table, self.attention1, self.attention2)

    def choose_items(self):
        if self.table:
            self.attention1 = sample1(self.table)
        else:
            raise WorldException
        new_table = copy(self.table)
        new_table.remove(self.attention1)
        if new_table:
            self.attention2 = sample1(new_table)
        else:
            raise WorldException
        return self

    def pick_smaller(self):
        if self.attention1 and self.attention2 and self.attention2.top.size >= self.attention1.bottom.size:
            tmp = self.attention1
            self.attention1 = self.attention2
            self.attention2 = tmp
        return self

    def stack(self):
        if self.attention1 and self.attention2 and self.attention1.top.size >= self.attention2.bottom.size:
            self.table.remove(self.attention1)
            self.table.remove(self.attention2)
            self.table.add(Stack(parts=[self.attention1,self.attention2]))
            self.attention1 = None
            self.attention2 = None
            return self
        else:
            raise WorldException

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib import break_ctrlc
from LOTlib.Miscellaneous import Infinity, q, attrmem
#from LOTlib.Hypotheses.RecursiveLOTHypothesis import RecursiveLOTHypothesis
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

class StackerHypothesis(LOTHypothesis):

    def __init__(self, grammar=grammar, **kwargs):
        LOTHypothesis.__init__(self, grammar=grammar, display='lambda s: %s', **kwargs)

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

        return max([s.height for s in ws.table])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

# we use a low likelihood_temperature to count the data more by favoring higher likelihoods
for h in break_ctrlc(MHSampler(StackerHypothesis(), [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.5)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
