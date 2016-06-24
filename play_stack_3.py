
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A desired program:
#
# recurse_((ws.stack() if ws.pick_up('l').pick_up('r').tight_fit() else ws.put_down('r')).put_down('l'))
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 'ws',                 None,                     10.0) # the world state input
grammar.add_rule('STATE', 'recurse_',           ['STATE'],                1.0)  # recurse!
grammar.add_rule('STATE', '(%s if %s else %s)', ['STATE','BOOL','STATE'], 1.0)  # needs to short-circuit
grammar.add_rule('STATE', '%s.pick_up(%s)',     ['STATE','SIDE'],         1.0)  # put something in my hand
grammar.add_rule('STATE', '%s.put_down(%s)',    ['STATE','SIDE'],         1.0)  # put down the thing in my hand
grammar.add_rule('STATE', '%s.stack()',         ['STATE'],                1.0)  # stack what I'm holding (right on left)

grammar.add_rule('BOOL',  '%s.tight_fit()',     ['STATE'],                1.0)  # does what I'm holding fit nicely?

grammar.add_rule('SIDE',  '"l"',                None,                     1.0)  # the left side  (hand or table)
grammar.add_rule('SIDE',  '"r"',                None,                     1.0)  # the right side (hand or table)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cup
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cup(object):
    """cups have a size"""
    def __init__(self, size=1):
        self.__dict__.update(locals())

    def __repr__(self):
        return 'Cup(size=%s)' % self.size

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Stack
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Miscellaneous import Infinity, q, attrmem

class Stack(object):
    def __init__(self, parts=[]):
        self.__dict__.update(locals())
        self.the_height()
        self.the_top()
        self.the_bottom()
        
    def __repr__(self):
        return 'Stack(parts=%s)' % self.parts

    @attrmem('height')
    def the_height(self):
        return sum([1 if type(part) is Cup else part.height for part in self.parts])

    @attrmem('top')
    def the_top(self):
        if self.parts:
            part = self.parts[-1]
            return part if type(part) is Cup else part.the_top()
        else:
            raise WorldException

    @attrmem('bottom')
    def the_bottom(self):
        if self.parts:
            part = self.parts[0]
            return part if type(part) is Cup else part.the_bottom()
        else:
            raise WorldException

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
        self.table = { Stack([Cup(n)]) for n in xrange(10) }
        self.hands = { 'l' : None, 'r' : None }

    def __str__(self):
        return '[%s, %s]'  % (self.table, self.hands)

    def pick_up(self,hand):
        if self.hands[hand] is None and self.table:
            self.hands[hand] = sample1(self.table)
            self.table.remove(self.hands[hand])
            return self
        else:
            raise WorldException
        
    def put_down(self,hand):
        if self.hands[hand] is not None:
            self.table.add(self.hands[hand])
            self.hands[hand] = None 
            return self
        else:
            raise WorldException
    
    def tight_fit(self):
        if self.full_hand('l') and self.full_hand('r'):
            return self.hands['l'].top.size - self.hands['r'].bottom.size == 1
        else:
            raise WorldException

    def loose_fit(self):
        if self.full_hand('l') and self.full_hand('r'):
            return self.hands['l'].top.size - self.hands['r'].bottom.size >= 1
        else:
            raise WorldException

    def empty_hand(self,hand):
        return (self.hands[hand] is None)

    def full_hand(self,hand):
        return (self.hands[hand] is not None)

    def empty_table(self,hand):
        return (self.table == set())
        
    def full_table(self,hand):
        return (self.table != set())
    
    def stack(self): # stack right on top of left
        if self.full_hand('r') and self.full_hand('l') and self.loose_fit():
            self.hands['l'] = Stack(parts = [ self.hands['l'], self.hands['r'] ])
            self.hands['r'] = None
            return self
        else:
            raise WorldException

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib import break_ctrlc
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

        return max([s.height for s in ws.table])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == '__main__':

    from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

    h0 = StackerHypothesis()

    # we use a low likelihood_temperature to count the data more (i.e. favor higher likelihoods?)
    for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.001)):
        print h.posterior_score, h.prior, h.likelihood, q(h)
