# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Model 3:
#
# This is a pretty basic stacking model. We're interested in capturing
# only the first two stages in the (Greenfield, et al., 1972)
# progression: 1) creating a stack of two objects; and 2) recursively
# adding to this stack. We're ignoring the third stage for now.
#
# The problem, again, seems to be learning sub-parts. Until we can do
# that, we can't do much. How would I do that in LOTlib? I can use
# lambdas, lexicons, or some alternative strategy that modifies the
# grammar directly. I suppose the place to start tomorrow is to look
# at the lexicon-based approach and then consider a hackier approach
# based on tweaking the grammar.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# recurse_( s.choose_stack_as_base().choose_hand().grasp().add_cup_to_stack() if s.stack_on_table() else s.choose_cup_as_base().choose_hand().grasp().stack_cups())

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                         None,      10.0)
grammar.add_rule('STATE', 'recurse_',                  ['STATE'],      1.0)
grammar.add_rule('STATE', '(%s if %s else %s)',        ['STATE','BOOL','STATE'],      1.0)
grammar.add_rule('STATE', '%s.choose_stack_as_base()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_cup_as_base()',   ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_hand()',      ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.grasp()',            ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack_cups()',       ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.add_cup_to_stack()', ['STATE'], 1.0)

grammar.add_rule('BOOL', '%s.stack_on_table()', ['STATE'], 1.0)
grammar.add_rule('BOOL', '%s.cup_on_table()',   ['STATE'], 1.0)

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

    def cup_on_table(self):
        for x in self.table:
            if isinstance(x,Cup):
                return True
        return False
    
    def stack_on_table(self):
        for x in self.table:
            if isinstance(x,Stack):
                return True
        return False

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
            if self.holding:
                self.table.add(self.holding)
                self.holding = None
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
from LOTlib.Hypotheses.RecursiveLOTHypothesis import RecursiveLOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

def get_height(x):
    return x.height if isinstance(x,Stack) else 1

class StackerHypothesis(RecursiveLOTHypothesis):

    def __init__(self, grammar=grammar, **kwargs):
        RecursiveLOTHypothesis.__init__(self, grammar=grammar, display='lambda recurse_, s: %s', **kwargs)

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

        #return max([get_height(s) for s in ws.table])
        return sum([get_height(s)*(get_height(s)+1)/2 for s in ws.table])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

for h in break_ctrlc(MHSampler(StackerHypothesis(),
                               [],
                               steps=100000,
                               skip=100,
                               prior_temperature=1.0,
                               likelihood_temperature=0.001)): # low temp favors higher likelihood
    print h.posterior_score, h.prior, h.likelihood, q(h)
