
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A desired program:
#
# recurse_(if_(ws.started(),
#              if_(ws.pick_up("left","right").tight_fit("left"),
#                  ws.stack("left"),
#                  ws),
#              if_(ws.table_empty("left"),
#                  ws.stack("left"),
#                  if_(ws.pick_up("left","left").pick_up("right").bigger("right"),
#                      ws.set_down("left","right").swap_hands(),
#                      ws.set_down("right","right")))))
#
# or, to cheat at the start:
#
# recurse_(((x.stack('l')
#            if x.pick_up('l','l').tight_fit('l')
#            else x.set_down('l','l'))
#           if x.started()
#           else x.start_it()))
#
# OR
#
# ((recurse_(x.stack('l'))
#   if x.pick_up('l','l').tight_fit('l')
#   else recurse_(x.set_down('l','l')))
#  if x.started()
#  else recurse_(x.start_it())))
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 'ws',                 None,                     10.0) # the world-state input
grammar.add_rule('STATE', '(%s if %s else %s)', ['STATE','BOOL','STATE'], 1.0)  # needs to short-circuit
grammar.add_rule('STATE', 'recurse_',           ['STATE'],                1.0)  # the recursive call
grammar.add_rule('STATE', '%s.pick_up(%s,%s)',   ['STATE','SIDE','SIDE'], 1.0)  # pick things up...
grammar.add_rule('STATE', '%s.set_down(%s,%s)', ['STATE','SIDE','SIDE'],  1.0)  # ...and put them down
grammar.add_rule('STATE', '%s.stack(%s)',       ['STATE','SIDE'],         1.0)  # put things on the solution stack
#grammar.add_rule('STATE', '%s.swap_hands()',    ['STATE'],                1.0)  # switch what your holding
grammar.add_rule('STATE', '%s.start_it()',      ['STATE'],                1.0)  # find the biggest thing and stack it

grammar.add_rule('BOOL',  '%s.started()',       ['STATE'],                1.0)  # do I have a stack?
grammar.add_rule('BOOL',  '%s.tight_fit(%s)',   ['STATE','SIDE'],         1.0)  # does this thing fit on the stack?
#grammar.add_rule('BOOL',  '%s.bigger(%s)',      ['STATE','SIDE'],         1.0)  # is the thing in this hand bigger?
#grammar.add_rule('BOOL',  '%s.table_empty(%s)', ['STATE','SIDE'],         1.0)  # is there anything on the table?
#grammar.add_rule('BOOL',  '%s.hand_empty(%s)',  ['STATE','SIDE'],         1.0)  # is there anything in my hand?

grammar.add_rule('SIDE',  '"l"',                None,                     1.0)  # the left side  (hand or table)
#grammar.add_rule('SIDE',  '"r"',                None,                     1.0)  # the right side (hand or table)

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
# WorldState
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from numpy.random import geometric

class WorldException(Exception):
    pass

class WorldState(object):
    """the world state - most functions should return worldstates (usually self)"""
    def __init__(self):
        self.table = { 'l' : { Cup(size=n) for n in xrange(10) }, 'r' : set() }
        self.hands = { 'l' : None, 'r' : None }
        self.solution = []

    def __str__(self):
        return '[%s, %s, %s]'  % (self.hands, self.table, self.solution)

#    def pick_up(self,hand,table):
#        """selects the *approximately largest* item in the set"""
#        if self.hands[hand] is None and self.table[table]:
#            cups = sorted(self.table[table],key=(lambda x: x.size),reverse=True)
#            self.hands[hand] = cups[min(geometric(.6),len(self.table[table]))-1]
#            self.table[table].remove(self.hands[hand])
#            return self
#        else:
#            raise WorldException

    def pick_up(self,hand,table):
        """selects a *random* item in the set"""
        if self.hands[hand] is None and self.table[table]:
            self.hands[hand] = sample1(self.table[table])
            self.table[table].remove(self.hands[hand])
            return self
        else:
            raise WorldException

    def set_down(self,hand,table):
        if self.hands[hand] is not None:
            self.table[table].add(self.hands[hand])
            self.hands[hand] = None
            return self
        else:
            raise WorldException
            
    def stack(self,hand):
        if self.hands[hand] is not None and self.solution != [] and self.solution[-1].size >= self.hands[hand].size:
            self.solution.append(self.hands[hand])
            self.hands[hand] = None
            return self
        else:
            raise WorldException

    def start_it(self):
        if not self.started():
            options = self.table['l'].union(self.table['r'])
            biggest_cup = max(options,key=(lambda x: x.size))
            self.solution.append(biggest_cup)
            if biggest_cup in self.table['l']:
                self.table['l'].remove(biggest_cup)
            else:
                self.table['r'].remove(biggest_cup)
            return self
        else:
            raise WorldException
        
    def swap_hands(self):
        tmp = self.hands['l']
        self.hands['l'] = self.hands['r']
        self.hands['r'] = tmp
        return self

    def tight_fit(self,hand):
        if self.hands[hand] is not None and self.solution != []:
            return self.solution[-1].size - self.hands[hand].size == 1
        else:
            raise WorldException

    def loose_fit(self,hand):
        if self.hands[hand] is not None and self.solution != []:
            return self.solution[-1].size >= self.hands[hand].size
        else:
            raise WorldException
        
    def bigger(self,hand):
        if self.hands['l'] and self.hands['r']:
            return max(self.hands.keys(),key=lambda x: self.hands[x].size) == hand
        else:
            raise WorldException

    def hand_empty(self,hand):
        return self.hands[hand] is None
    
    def started(self):
        return (self.solution != [])

    def table_empty(self,table):
        return self.table[table] == set()

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
        return len(ws.solution)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

# we use a low likelihood_temperature to count the data more (i.e. favor higher likelihoods?)
for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.001)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
