
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='WORLD-STATE')

grammar.add_rule('WORLD-STATE', '%s.stack()',           ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.left_grab(%s)',     ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.right_grab(%s)',    ['WORLD-STATE', 'OBJECT'], 1.0)
grammar.add_rule('WORLD-STATE', '%s.left_drop()',       ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.right_drop()',      ['WORLD-STATE'],           1.0)

grammar.add_rule('WORLD-STATE', 'ws',                   None,                      10.0)
grammar.add_rule('WORLD-STATE', 'if_',                  ['BOOL', 'WORLD-STATE', 'WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', 'recurse_',             ['WORLD-STATE'],           1.0)

grammar.add_rule('OBJECT',      '%s.choose_random()',   ['WORLD-STATE'],           5.0)
grammar.add_rule('OBJECT',      '%s.the_left_hand()',   ['WORLD-STATE'],           1.0)
grammar.add_rule('OBJECT',      '%s.the_right_hand()',  ['WORLD-STATE'],           1.0)
grammar.add_rule('OBJECT',      '%s.top(%s)',           ['WORLD-STATE','OBJECT'],  1.0)
grammar.add_rule('OBJECT',      '%s.bottom(%s)',        ['WORLD-STATE','OBJECT'],  1.0)

grammar.add_rule('BOOL',        '%s.tight_fitP(%s,%s)', ['WORLD-STATE','OBJECT','OBJECT'],       1.0)
grammar.add_rule('BOOL',        '%s.loose_fitP(%s,%s)', ['WORLD-STATE','OBJECT','OBJECT'],       1.0)
grammar.add_rule('BOOL',        '%s.same_cupP(%s,%s)',  ['WORLD-STATE','OBJECT','OBJECT'],       1.0)
grammar.add_rule('BOOL',        '%s.topP(%s)',          ['WORLD-STATE','OBJECT'],  1.0)
grammar.add_rule('BOOL',        '%s.bottomP(%s)',       ['WORLD-STATE','OBJECT'],  1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Worlds & Cups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from copy import deepcopy

class Cup(object):
    """cups have a top size,a bottom size, and 2D coordinates)"""
    def __init__(self, size=1, top=None, bottom=None):
        self.__dict__.update(locals())

    def __str__(self):
        return '(%s, t:%s, b:%s)' % (self.size, self.top, self.bottom)

class WorldException(Exception):
    pass

class WorldState(object):
    """
    Capture the world state. Most functions should return worldstates.

    """

    def __init__(self):
        self.table =  { n : Cup(size=n) for n in xrange(10) }
        self.left_hand  = None
        self.right_hand = None

    def __str__(self):
        f = lambda x: str({k : str(v) for k,v in x.iteritems()}) if x else str(x)
        return '[%s, %s, %s]'  % (f(self.left_hand), f(self.right_hand), f(self.table))

    def the_left_hand(self):
        if self.left_hand is None:
            raise WorldException
        else:
            return [k for k,v in self.left_hand.iteritems() if v.bottom is None][0]

    def the_right_hand(self):
        if self.right_hand is None:
            raise WorldException
        else:
            return [k for k,v in self.right_hand.iteritems() if v.bottom is None][0]

    def left_grab(self, x):
        s = deepcopy(self)
        if x in s.table and type(s.table[x]) is Cup and s.left_hand is None:

            # add the object to your hand
            s.left_hand = {x : s.table[x]}

            # sever the attachment if needed
            if s.left_hand[x].bottom:
                s.table[s.left_hand[x].bottom].top = None
                s.left_hand[x].bottom = None

            # remove it from the table
            del s.table[x]

            # add the things on top of it to your hand and remove them from the table
            while s.left_hand[x].top is not None:
                x = s.left_hand[x].top
                s.left_hand[x] = s.table[x]
                del s.table[x]

        else:
            raise WorldException
        
        return s

    def right_grab(self, x):
        s = deepcopy(self)
        if x in s.table and type(s.table[x]) is Cup and s.right_hand is None:
            
            # add the object to your hand
            s.right_hand = {x : s.table[x]}

            # sever the attachment if needed
            if s.right_hand[x].bottom:
                s.table[s.right_hand[x].bottom].top = None
                s.right_hand[x].bottom = None

            # remove it from the table
            del s.table[x]

            # add the things on top of it to your hand and remove them from the table
            while s.right_hand[x].top is not None:
                x = s.right_hand[x].top
                s.right_hand[x] = s.table[x]
                del s.table[x]

        else:
            raise WorldException
        
        return s

    def left_drop(self):
        s = deepcopy(self)
        if s.left_hand is not None:
            s.table.update(s.left_hand)
            s.left_hand = None
        else:
            raise WorldException
        return s

    def right_drop(self):
        s = deepcopy(self)
        if s.right_hand is not None:
            s.table.update(s.right_hand)
            s.right_hand = None
        else:
            raise WorldException
        return s

    def stack(self):
        """ Put right hand on top of the left """
        s = deepcopy(self)
        # get what you're holding
        l, r = s.left_hand, s.right_hand

        # you must be holding two things
        if l and r:
            top    = [k for k,v in l.iteritems() if not v.top   ][0]
            bottom = [k for k,v in r.iteritems() if not v.bottom][0]
            if (r[bottom].size <= l[top].size):
                l[top].top = bottom
                r[bottom].bottom = top
                l.update(r)
                s.left_hand = l
                s.right_hand = None
        
        else:
            raise WorldException
        
        return s

    def choose_random(self):
        if len(self.table) >= 1:
            return sample1(self.table.keys())
        else:
            raise WorldException

    def find(self,x):
        if self.table is not None and x in self.table:
            return self.table[x]
        elif self.left_hand is not None and x in self.left_hand:
            return self.left_hand[x]
        elif self.right_hand is not None and x in self.right_hand:
            return self.right_hand[x]
        else:
            return None
        
    def top(self,x):
        y = self.find(x)
        if y is None or y.top is None:
            raise WorldException
        else:
            return y.top

    def bottom(self,x):
        y = self.find(x)
        if y is None or y.bottom is None:
            raise WorldException
        else:
            return y.bottom

    def topP(self,x):
        return self.top(x) is not None

    def bottomP(self,x):
        return self.bottom(x) is not None

    def tight_fitP(self,x,y):
        x = self.find(x)
        y = self.find(y)
        if x is None or y is None:
            raise WorldException
        else:
            return x.size-y.size == 1

    def loose_fitP(self,x,y):
        x = self.find(x)
        y = self.find(y)
        if x is None or y is None:
            raise WorldException
        else:
            return x.size-y.size > 1

    def same_cupP(self,x,y):
        return x == y

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

        return max([max_height(x) for x in [ws.table, ws.left_hand, ws.right_hand]])

def max_height(x):
    def height(k):
        count = 1
        while x[k].top:
            count +=1
            k = x[k].top
        return count
    return max([height(k) for k in x.iterkeys()]) if x else 0

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

# we use a low likelihood_temperature to count the data more (i.e. favor higher likelihoods?)
for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.01)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
