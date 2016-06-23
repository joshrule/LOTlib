
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A desired program:
#
# recurse_(
#   if_(
#     and_(
#       tight_fit(
#         getattr(ws.left_grab(ws.choose_random()).the_left_hand(),  "size",None),
#         getattr(ws.right_grab(ws.choose_random()).the_right_hand(),"size",None))
#       ws.the_left_hand().topP()
#     ),
#     ws.stack().left_drop(),
#     ws.left_drop().right_drop()))
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='WORLD-STATE')

grammar.add_rule('WORLD-STATE', 'ws',                   None,                      10.0)
grammar.add_rule('WORLD-STATE', 'if_',                  ['BOOL', 'WORLD-STATE', 'WORLD-STATE'], 1.0)
grammar.add_rule('WORLD-STATE', 'recurse_',             ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.stack()',           ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.left_grab(%s)',     ['WORLD-STATE', 'CUP'],    1.0)
grammar.add_rule('WORLD-STATE', '%s.right_grab(%s)',    ['WORLD-STATE', 'CUP'],    1.0)
grammar.add_rule('WORLD-STATE', '%s.left_drop()',       ['WORLD-STATE'],           1.0)
grammar.add_rule('WORLD-STATE', '%s.right_drop()',      ['WORLD-STATE'],           1.0)

grammar.add_rule('CUP',         '%s.choose_random()',   ['WORLD-STATE'],           1.0)
grammar.add_rule('CUP',         '%s.the_left_hand()',   ['WORLD-STATE'],           1.0)
grammar.add_rule('CUP',         '%s.the_right_hand()',  ['WORLD-STATE'],           1.0)
#grammar.add_rule('CUP',         '%s.top(%s)',           ['WORLD-STATE','CUP'],     1.0)
#grammar.add_rule('CUP',         '%s.bottom(%s)',        ['WORLD-STATE','CUP'],     1.0)

grammar.add_rule('SIZE',        'getattr(%s,"size",None)', ['CUP'],                1.0)

grammar.add_rule('BOOL',        'tight_fit(%s,%s)',    ['SIZE','SIZE'],        1.0)
#grammar.add_rule('BOOL',        'loose_fit(%s,%s)',    ['SIZE','SIZE'],        1.0)
grammar.add_rule('BOOL',        '%s.topP()',           ['CUP'],  1.0)
#grammar.add_rule('BOOL',        '%s.bottomP()',        ['CUP'],  1.0)
grammar.add_rule('BOOL',        'and_',                ['BOOL','BOOL'],  1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Worlds & Cups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cup(object):
    """cups have a size, and be on top of or under another cup)"""
    def __init__(self, id=0, size=1, top=None, bottom=None):
        self.__dict__.update(locals())

    def __str__(self):
        return '(%s, %s, t:%s, b:%s)' % (self.id, self.size, self.top, self.bottom)

    def topP(self): # am I on top?
        return self.top is None

    def bottomP(self): # am I on bottom?
        return self.bottom is None

from LOTlib.Eval import primitive

@primitive
def tight_fit(x,y):
    if x is None or y is None:
        raise WorldException
    else:
        return x-y == 1

@primitive
def loose_fit(x,y):
    if x is None or y is None:
        raise WorldException
    else:
        return x-y >  1
    
class WorldException(Exception):
    pass

class WorldState(object):
    """Capture the world state. Most functions should return worldstates."""
    def __init__(self):
        self.table =  { n : Cup(id=n,size=n) for n in xrange(10) }
        self.left_hand  = None
        self.right_hand = None

    def __str__(self):
        f = lambda x: str({k : str(v) for k,v in x.iteritems()}) if x else str(x)
        return '[%s, %s, %s]'  % (f(self.left_hand), f(self.right_hand), f(self.table))

    def the_left_hand(self):
        if self.left_hand is None:
            raise WorldException
        else:
            return [v for v in self.left_hand.itervalues() if v.bottom is None][0]

    def the_right_hand(self):
        if self.right_hand is None:
            raise WorldException
        else:
            return [v for v in self.right_hand.itervalues() if v.bottom is None][0]

    def left_grab(self, x):
        if x.id in self.table and self.left_hand is None:

            # add the object to your hand
            self.left_hand = {x.id : x}

            # sever the attachment if needed
            if x.bottom:
                self.table[x.bottom].top = None
                self.left_hand[x.id].bottom = None

            # remove it from the table
            del self.table[x.id]

            # add the things on top of it to your hand and remove them from the table
            while x.top is not None:
                x = self.table[x.top]
                self.left_hand[x.id] = x
                del self.table[x.id]

        else:
            raise WorldException
        
        return self

    def right_grab(self, x):
        if x in self.table and self.right_hand is None:
            
            # add the object to your hand
            self.right_hand = {x.id : x}

            # sever the attachment if needed
            if x.bottom:
                self.table[x.bottom].top = None
                self.right_hand[x.id].bottom = None

            # remove it from the table
            del self.table[x.id]

            # add the things on top of it to your hand and remove them from the table
            while x.top is not None:
                x = self.table[x.top]
                self.right_hand[x.id] = x
                del self.table[x.id]

        else:
            raise WorldException
        
        return self

    def left_drop(self):
        if self.left_hand is not None:
            self.table.update(self.left_hand)
            self.left_hand = None
        else:
            raise WorldException
        return self

    def right_drop(self):
        if self.right_hand is not None:
            self.table.update(self.right_hand)
            self.right_hand = None
        else:
            raise WorldException
        return self

    def stack(self):
        """ Put right hand on top of the left """
        # get what you're holding
        l, r = self.left_hand, self.right_hand

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
            
        else:
            raise WorldException
        
        return self

    def choose_random(self):
        if len(self.table) >= 1:
            return sample1(self.table.values())
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
        if x.top is None:
            raise WorldException
        else:
            return self.find(x.top)

    def bottom(self,x):
        if x.bottom is None:
            raise WorldException
        else:
            return self.find(x.bottom)

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
for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.001)):
    print h.posterior_score, h.prior, h.likelihood, q(h)
