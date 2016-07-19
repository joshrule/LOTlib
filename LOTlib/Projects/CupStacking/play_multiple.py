# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar
#
# A model of cup stacking which learns the representation it should
# use. It does so by breaking the problem into two parts (though could
# be rewritten for a configurable number of parts). We essentially
# split the grammar so that there are two languages with a bridge
# non-terminal between them. At a high-level, how would I solve the
# problem this way as an adult? I would first take each cup and turn
# it into a stack. There's no such object as a stack, but I have the
# concept. So, I would turn each item into a stack. I would then go
# about using the stack-based solution to the problem in my second
# function. It would look something like this:
#
# solve_stacking_problem(convert_cups_to_stacks(raw_data))
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar

grammar = Grammar(start='WORLD-STATE')

# notice that we only access the world (ws) as an argument

# the cup model:
grammar.add_rule('WORLD-STATE', '(%s)(ws)', ['CUPFUNC'], 1.0)
grammar.add_rule('CUPFUNC', 'lambda', ['CUP-STATE'], 1.0, bv_type='CUP-STATE', bv_p=10.0)

grammar.add_rule('CUP-STATE', 'if_',                  ['CUP-BOOL', 'CUP-STATE', 'CUP-STATE'], 1.0)
grammar.add_rule('CUP-STATE', 'recurse_',             ['CUP-STATE'],           1.0)
grammar.add_rule('CUP-STATE', '%s.stack()',           ['CUP-STATE'],           1.0)
grammar.add_rule('CUP-STATE', '%s.left_grab(%s)',     ['CUP-STATE', 'CUP'],    1.0)
grammar.add_rule('CUP-STATE', '%s.right_grab(%s)',    ['CUP-STATE', 'CUP'],    1.0)
grammar.add_rule('CUP-STATE', '%s.left_drop()',       ['CUP-STATE'],           1.0)
grammar.add_rule('CUP-STATE', '%s.right_drop()',      ['CUP-STATE'],           1.0)

grammar.add_rule('CUP',         '%s.choose_random()',   ['CUP-STATE'],           1.0)
grammar.add_rule('CUP',         '%s.the_left_hand()',   ['CUP-STATE'],           1.0)
grammar.add_rule('CUP',         '%s.the_right_hand()',  ['CUP-STATE'],           1.0)

grammar.add_rule('CUP-SIZE',        'getattr(%s,"size",None)', ['CUP'],                1.0)

grammar.add_rule('CUP-BOOL',        'tight_fit(%s,%s)', ['CUP-SIZE','CUP-SIZE'],  1.0)
grammar.add_rule('CUP-BOOL',        'loose_fit(%s,%s)', ['CUP-SIZE', 'CUP-SIZE'], 1.0)
grammar.add_rule('CUP-BOOL',        'and_',             ['CUP-BOOL','CUP-BOOL'],  1.0)

# the stack model:
# this bit's obfuscated and uses typecasting in several rules
grammar.add_rule('WORLD-STATE', '(%s)((%s)(ws))', ['STATEFUNC', 'STACKMAKER'], 1.0)
grammar.add_rule('STATEFUNC',  'lambda', ['STACK-OUT'], 1.0, bv_type='STACK-STATE', bv_p=10.0)
grammar.add_rule('STACKMAKER', 'lambda', ['STACK-IN'],  1.0, bv_type='INPUT',       bv_p=10.0)
grammar.add_rule('STACK-IN', '%s.make_stacks()', ['INPUT'], 1.0)

grammar.add_rule('STACK-STATE', 'if_',                            ['STACK-BOOL', 'STACK-STATE', 'STACK-STATE'], 1.0)
grammar.add_rule('STACK-OUT',   'recurse_',                       ['STACK-OUT'],            1.0)
grammar.add_rule('STACK-STATE', '%s.stack()',                     ['STACK-STATE'],          1.0)
grammar.add_rule('STACK-STATE', '%s.left_grab(%s)',               ['STACK-STATE', 'STACK'], 1.0)
grammar.add_rule('STACK-STATE', '%s.right_grab(%s)',              ['STACK-STATE', 'STACK'], 1.0)
grammar.add_rule('STACK-STATE', '%s.left_drop()',                 ['STACK-STATE'],          1.0)
grammar.add_rule('STACK-STATE', '%s.right_drop()',                ['STACK-STATE'],          1.0)
grammar.add_rule('STACK-OUT',   '%s.do()',                        ['STACK-STATE'],          1.0)

grammar.add_rule('STACK',       '%s.choose_random()',             ['STACK-STATE'],          1.0)
grammar.add_rule('STACK',       'getattr(%s,"left_hand",None)',   ['STACK-STATE'],          1.0)
grammar.add_rule('STACK',       'getattr(%s,"right_hand",None)',  ['STACK-STATE'],          1.0)

grammar.add_rule('STACK-SIZE',        'getattr(%s,"top_size",None)',    ['STACK'],                1.0)
grammar.add_rule('STACK-SIZE',        'getattr(%s,"bottom_size",None)', ['STACK'],                1.0)

grammar.add_rule('STACK-BOOL',        'tight_fit(%s,%s)', ['STACK-SIZE','STACK-SIZE'],  1.0)
grammar.add_rule('STACK-BOOL',        'loose_fit(%s,%s)', ['STACK-SIZE', 'STACK-SIZE'], 1.0)
grammar.add_rule('STACK-BOOL',        'and_',             ['STACK-BOOL','STACK-BOOL'],  1.0)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Cups & Stacks
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cup(object):
    """cups have a size"""
    def __init__(self, size=1):
        self.__dict__.update(locals())

    def __str__(self):
        return 'size: %d' % self.size

class Stack(object):
    """stacks have a height, a top and bottom size, and constituent parts.
    Rather than a list of cups, it's a list of components, which could
    themselves be stacks (i.e. hierarchical nesting).

    """

    def __init__(self, parts=[]):
        self.parts=parts
        self.height = sum([1 if is_cup(x) else x.height for x in parts])
        self.top_size = parts[-1].size if is_cup(parts[-1]) else parts[-1].top_size
        self.bottom_size = parts[0].size if is_cup(parts[0]) else parts[0].bottom_size

    def __str__(self):
        return 'h:%d, b:%d, t:%d - %s' % (self.height, self.bottom_size, self.top_size, str(self.parts))

    def bottom(self):
        return self.parts[0]

    def top(self):
        return self.parts[-1]

    def unstack_once(self):
        return self.parts

    def unstack(self):
        unstack =  [x if is_cup(x) else x.unstack() for x in self.parts]
        return unstack[0] if len(unstack) is 1 else unstack

from LOTlib.Eval import primitive

@primitive
def is_cup(x):
    return type(x) is Cup

@primitive
def is_stack(x):
    return type(x) is Stack

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
        return x-y > 1

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# World/Cup State
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
class WorldException(Exception):
    pass

# all following assumes we have uniquely sized cups
class WorldState(object): # also serves as the cup state

    def __init__(self,table=[],left=[],right=[]):
        self.table = [Cup(size=n) for n in xrange(10)] if table == [] else table
        self.left_hand  = left
        self.right_hand = right

    def __str__(self):
        return '[%s, %s, %s]' % (self.left_hand, self.right_hand, self.table)

    def make_stacks(self):
        catch_singletons = lambda xs: [x if type(x) is list else [x] for x in xs]
        return StackState(table = catch_singletons(self.table),
                          left  = catch_singletons(self.left_hand),
                          right = catch_singletons(self.right_hand))


    def hand(self,which):
        the_hand = getattr(self,which+"_hand",None)
        if the_hand:
            return max(the_hand,key=(lambda x: x.size))
        else:
            raise WorldException
    
    def the_left_hand(self):
        return self.hand("left")

    def the_right_hand(self):
        return self.hand("right")
        
    def grab(self,x,which):
        if not getattr(self,which+"_hand",None):
            # find the stack the item's in
            idx = None
            for v,i in enumerate(self.table):
                if (is_cup(v) and x is v) or (type(v) is list and x in v):
                    idx = i

            # actually pick up the object (and what's on top of it
            if idx and is_cup(self.table[i]):
                self.table.remove(x)
                setattr(self,which+"_hand",x)
                
            if idx and type(self.table[i]) is list:
                to_leave = [v for v in self.table[i] if v.size > x.size]
                to_take = [v for v in self.table[i] if v.size <= x.size]
                self.table[i] = to_leave
                setattr(self,which+"_hand",to_take)

        else:
            raise WorldException
        
        return self

    def left_grab(self, x):
        return self.grab(x,"left")

    def right_grab(self, x):
        return self.grab(x,"right")

    def drop(self,which):
        if getattr(self,which+"_hand",None) is not None:
            self.table += [getattr(self,which+"_hand",None)]
            setattr(self,which+"_hand",None)
        else:
            raise WorldException
        return self

    def left_drop(self):
        return self.drop("left")

    def right_drop(self):
        return self.drop("right")

    def stack(self):
        """ Put right hand on top of the left """
        l, r = self.left_hand, self.right_hand

        if l and r and (min(l,lambda x: x.size).size >= max(r,lambda x: x.size).size):
            self.left_hand = l+r
            self.right_hand = None
            return self
                
        else:
            raise WorldException
        
    def choose_random(self):
        items = []
        for v in self.table:
            if is_cup(v):
                items += [v]
            else:
                items += v
        if len(items) >= 1:
            return sample1(items)
        else:
            raise WorldException

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# StackState
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class StackState(object):
    """
    Capture the world state using Stacks. By default, everything should return a stackstate (self is okay)

    """

    def __init__(self,table=[],left=[],right=[]):
        table = [[Cup(size=n)] for n in xrange(10)] if table == [] else table
        self.table =  [Stack(parts=s) for s in table]
        self.left_hand  = left
        self.right_hand = right

    def __str__(self):
        return '[%s, %s, %s]'  % (self.left_hand, self.right_hand, str([x.height for x in self.table]))

    def do(self):
        return WorldState(table = [x.unstack() for x in self.table],
                          left  = [x.unstack() for x in self.left_hand],
                          right = [x.unstack() for x in self.right_hand])
    
    def grab(self,x,which):
        if x in self.table and x is not None and getattr(self,which+"_hand",None) is None:
            setattr(self,which+"_hand",x)
            self.table.remove(x)
        else:
            raise WorldException
        return self
            
    def left_grab(self, x):
        return self.grab(x,"left")

    def right_grab(self, x):
        return self.grab(x,"right")

    def drop(self,which):
        if getattr(self,which+"_hand",[]):
            self.table.add(getattr(self,which+"_hand",[]))
            setattr(self,which+"_hand",[])
            return self
        else:
            raise WorldException

    def left_drop(self):
        return self.drop("left")

    def right_drop(self):
        return self.drop("right")

    def stack(self):
        """ Put right hand on top of the left """
        l, r = self.left_hand, self.right_hand

        if not is_stack(l) or not is_stack(r) or (r.bottom_size >= l.top_size):  # can't put something on top of itself:
            raise WorldException
        else:
            self.left_hand = Stack(l.parts+r.parts)
            self.right_hand = []

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
            return -100
        except WorldException:
            pass

        return max([max_height(x) for x in [ws.table, ws.left_hand, ws.right_hand]])

def max_height(x):
    height = lambda k: 1 if is_cup(k) else len(k)

    return 0 if ((x is None) or (x == [])) else max([height(v) for v in x])
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler

h0 = StackerHypothesis()

# we use a low likelihood_temperature to count the data more (i.e. favor higher likelihoods?)
for h in break_ctrlc(MHSampler(h0, [], steps=100000, skip=100, prior_temperature=1.0, likelihood_temperature=0.001)):
    print '{:.2f} {:.2f} {:.2f} {}'.format(h.posterior_score, h.prior, h.likelihood, q(h))
