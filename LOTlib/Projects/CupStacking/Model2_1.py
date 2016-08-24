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
# This approach seems to make it complicated enough to stack two items
# on top of each other that stacking a third doesn't happen easily. I
# got to this point by just splitting each subroutine into smaller
# subroutines.
#
# This model makes a sharp distinction between cups and stacks, which
# is part of what makes search difficult. The model must decide not
# only which actions to take and in what order, but what types of
# objects it would like to include in each operation: stacks, cups, or
# a suitable mix of both.
#
# That's fine for now, but how does it affect the second and third
# stages of the algorithm? The second stage is one in which you can
# create the initial stack and then choose cups one at a time to add
# to that stack. The third stage is one in which you can create the
# initial stack, and *either* choose cups one at a time to add to that
# stack, or choose to manipulate the stack directly. If manipulating
# the stack directly, you can pick it up and put it on another stack
# or on a cup.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                     None,      10.0)
grammar.add_rule('STATE', '%s.choose_stack_as_base()',      ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_cup_as_base()',      ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_hand()',      ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.grasp()',            ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack_cups()',       ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.add_cup_to_stack()', ['STATE'], 1.0)

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
        self.table =  { Cup(n) for n in xrange(10) }
        self.base = None
        self.hand = None
        self.holding = None

    def __str__(self):
        return '[%s, %s, %s]'  % (self.table, self.attention1, self.attention2)

    def choose_stack_as_base(self):
        filtered_table = [x for x in self.table if isinstance(x,Stack)]
        if filtered_table:
            self.base = sample1(filtered_table)
            return self
        else:
            raise WorldException
        
    def choose_cup_as_base(self):
        filtered_table = [x for x in self.table if isinstance(x,Cup)]
        if filtered_table:
            self.base = sample1(filtered_table)
            return self
        else:
            raise WorldException

    def choose_hand(self):
        if self.table:
            self.hand = sample1(self.table)
            return self
        else:
            raise WorldException

    def grasp(self):
        if self.hand:
            self.holding = self.hand
            self.table.remove(self.hand)
            self.hand = None
            return self
        else:
            raise WorldException

    def stack_cups(self):
        if self.base and self.holding and isinstance(self.base,Cup) and isinstance(self.holding,Cup) and self.base.size <= self.holding.size and self.base != self.holding and self.base in self.table:
            new_stack = Stack(parts=[self.base, self.holding])
            self.table.remove(self.base)
            self.holding = None
            self.base = None
            self.table.add(new_stack)
            return self
        else:
            raise WorldException

    def add_cup_to_stack(self):
        if self.base and self.holding and isinstance(self.base,Stack) and isinstance(self.holding,Cup) and self.base.top.size <= self.holding.size and self.base != self.holding and self.base in self.table:
            new_stack = Stack(parts=[self.base, self.holding])
            self.table.remove(self.base)
            self.holding = None
            self.base = None
            self.table.add(new_stack)
            return self
        else:
            raise WorldException

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib import break_ctrlc
from LOTlib.Miscellaneous import Infinity, q, attrmem
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

def get_height(x):
    return x.height if isinstance(x,Stack) else 1

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

        return max([get_height(s) for s in ws.table])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

for h in break_ctrlc(MHSampler(StackerHypothesis(),
                               [],
                               steps=100000,
                               skip=100,
                               prior_temperature=1.0,
                               likelihood_temperature=0.01)): # low temp favors higher likelihood
    print h.posterior_score, h.prior, h.likelihood, q(h)
