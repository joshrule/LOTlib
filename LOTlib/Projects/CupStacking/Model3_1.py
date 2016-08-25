# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Model 3_1:
#
# This is a pretty basic stacking model. We're interested in capturing
# only the first two stages in the (Greenfield, et al., 1972)
# progression: 1) creating a stack of two objects; and 2) recursively
# adding to this stack. We're ignoring the third stage for now.
#
# The problem we're trying to address with 3_1 over 3 is how to move
# from a formally correct grammar to one a combination of grammar and
# learning algorithm that will successfully master the problem. What's
# wrong with the learning algorithm? We need to learn the program
# below:
#
# recurse_( s.choose_stack_as_base().choose_hand().grasp().add_cup_to_stack() if s.stack_on_table() else s.choose_cup_as_base().choose_hand().grasp().stack_cups())
#
# That's a long program to find via a random walk and really consists
# of two major parts that could be glossed as something like: if the
# initial stack exists, add to the stack, else setup the initial
# stack. Moreover, there's significant shared structure between the
# two cases. So, if there's a way to favor that sort of sharing, or to
# make these larger but useful components less difficult to find, we
# want to take advantage of them.
#
# My first attempt at this will be to use a lexicon, just to see if
# that works at all. The idea here is that we'll setup a few
# placeholder functions and let the chain propose to them. We'll have
# one master function that we'll use to perform testing. The program
# learned there is the one we're interested in tracking over time. The
# other functions are just there to provide places to store ideas.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Lexicon setup
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

number_of_functions = 3
fs = ['f' + str(x) for x in range(number_of_functions)]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar
from LOTlib.Miscellaneous import q

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                         None,      10.0)
grammar.add_rule('STATE', '(%s if %s else %s)',        ['STATE','BOOL','STATE'],      1.0)
grammar.add_rule('STATE', '%s.choose_stack_as_base()', ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_cup_as_base()',   ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose_hand()',      ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.grasp()',            ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack_cups()',       ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.add_cup_to_stack()', ['STATE'], 1.0)

grammar.add_rule('BOOL', '%s.stack_on_table()', ['STATE'], 1.0)
grammar.add_rule('BOOL', '%s.cup_on_table()',   ['STATE'], 1.0)

for f in fs:
    grammar.add_rule('STATE', 'lexicon', [q(f), 'STATE'], 1.)

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
        if self.base and self.holding and isinstance(self.base,Cup) and isinstance(self.holding,Cup) and self.base.size >= self.holding.size and self.base != self.holding and self.base in self.table and not self.holding in self.table:
            new_stack = Stack(parts=[self.base, self.holding])
            self.table.remove(self.base)
            self.holding = None
            self.base = None
            self.hand = None
            self.table.add(new_stack)
            return self
        else:
            raise WorldException

    def add_cup_to_stack(self):
        if self.base and self.holding and isinstance(self.base,Stack) and isinstance(self.holding,Cup) and self.base.top.size >= self.holding.size and self.base != self.holding and self.base in self.table and not self.holding in self.table:
            new_stack = Stack(parts=[self.base, self.holding])
            self.table.remove(self.base)
            self.holding = None
            self.base = None
            self.hand = None
            self.table.add(new_stack)
            return self
        else:
            raise WorldException

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib.Miscellaneous import Infinity, attrmem
from LOTlib.Hypotheses.Lexicon.RecursiveLexicon import RecursiveLexicon
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

class StackerLikelihood(object):
    @attrmem('likelihood')
    def compute_likelihood(self, data, shortcut=None):
        assert len(data) == 0

        ws = WorldState()

        try:
            ws = self('f0',ws)

        except (TooBigException, RecursionDepthException):
            return -Infinity
        except WorldException:
            pass

        # likelihood favors stacking, particularly tall towers
        return sum([ sum(range((o.height if isinstance(o,Stack) else 1)+1)) for o in ws.table ])

class StackerLexicon(StackerLikelihood,RecursiveLexicon):
    pass

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
from LOTlib import break_ctrlc,SIG_INTERRUPTED
from LOTlib.Inference.Samplers.StandardSample import standard_sample
from LOTlib.MPI.MPI_map import MPI_unorderedmap, is_master_process
import itertools
import numpy

def run(make_hypothesis, make_data):
    if SIG_INTERRUPTED:
        return set()

    topCount = 100
    steps = 10000
    return standard_sample(make_hypothesis,
                           make_data,
                           N=topCount,
                           steps=steps,
                           show=False,
                           save_top=None,
                           prior_temperature=1.0,
                           likelihood_temperature=0.001)

def make_hypothesis(**kwargs):

    h = StackerLexicon(propose_p=0.25,**kwargs)

    for f in fs:
        h.set_word(f, LOTHypothesis(grammar, display='lambda lexicon, s: %s'))

    return h
    
def make_data():
    return []

if True:
    for h in break_ctrlc(MHSampler(make_hypothesis(),
                                   make_data(),
                                   steps=100000,
                                   skip=100,
                                   prior_temperature=1.0,
                                   likelihood_temperature=0.001)): # low temp favors higher likelihood
        print h.posterior_score, h.prior, h.likelihood, q(h)
else:
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
    
    import pickle
    with open('/home/rule/code/LOTlib/LOTlib/Projects/CupStacking/test.pkl', 'w') as f:
        pickle.dump(seen, f)

