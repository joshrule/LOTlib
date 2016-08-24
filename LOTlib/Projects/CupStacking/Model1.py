# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Model 1:
#
# This model is more complex than Model 0 but still stupidly simple.
# We're not even interested in being able to express the various
# stages through which kids might be able to go. At this point, we're
# just incrementally increasing the complexity. This model uses the
# extremely simple decomposition from Model 0, but with the added
# twist of now forcing the agent to choose what kind of fit to use.
#
# 1. Given the current state, find two objects that fit together
# 2. stack them
# 3. recurse
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A desired program:
#
# recurse_(ws.tight_fit().stack())
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                     None,      10.0)
grammar.add_rule('STATE', 'recurse_',              ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_tight_fit()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_loose_fit()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.fit_it()',           ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack()',            ['STATE'], 1.0)

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

    def __repr__(self):
        return 'Stack(parts=[%s])' % str([str(part) for part in self.parts])

    def top(self):
        if self.parts:
            part = self.parts[-1]
            return part if isinstance(part,Cup) else part.top()
        else:
            raise WorldException

    def bottom(self):
        if self.parts:
            part = self.parts[0]
            return part if isinstance(part,Cup) else part.bottom()
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
    def __init__(self,fit='loose'):
        self.table =  { Stack([Cup(n)]) for n in xrange(10) }
        self.attention1 = None
        self.attention2 = None
        self.fit = fit

    def __str__(self):
        return '[%s, %s, %s]'  % (self.table, self.attention1, self.attention2)

    def choose_loose_fit(self):
        self.fit = 'loose'
        return self

    def choose_tight_fit(self):
        self.fit = 'tight'
        return self
    
    def fit_it(self):
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
        if self.attention1 and self.attention2 and self.it_fits(self.attention1,self.attention2):
            return self
        elif self.fit_is_possible():
            return self.fit_it()
        else:
            raise WorldException

    def it_fits(self,s1,s2):
        if ((self.fit == 'loose' and s1.top().size - s2.bottom().size >= 1) or
            (self.fit == 'tight' and s1.top().size - s2.bottom().size == 1)):
            return True
        else:
            return False

    def fit_is_possible(self):
        for s1 in self.table:
            for s2 in self.table:
                if self.it_fits(s1,s2):
                    return True
        return False
    
    def stack(self):
        if self.attention1 and self.attention2 and self.attention1.top().size >= self.attention2.bottom().size:
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
from LOTlib.Hypotheses.RecursiveLOTHypothesis import RecursiveLOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

class StackerHypothesis(RecursiveLOTHypothesis):

    def __init__(self, grammar=grammar, **kwargs):
        RecursiveLOTHypothesis.__init__(self, grammar=grammar, display='lambda recurse_, s: %s', **kwargs) # for recursive hypotheses, must pass in recurse_

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
for h in break_ctrlc(MHSampler(StackerHypothesis(), [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.001)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
