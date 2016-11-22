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

number_of_functions = 4
fs = ['f' + str(x) for x in range(number_of_functions)]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Grammar:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from LOTlib.Grammar import Grammar
from LOTlib.Miscellaneous import q

grammar = Grammar(start='STATE')

grammar.add_rule('STATE', 's',                  None,      5.0)
grammar.add_rule('STATE', '(%s if %s else %s)', ['STATE','BOOL','STATE'], 1.0)
grammar.add_rule('STATE', '%s.choose(%s,%s)',   ['STATE','TYPE','FOR'],   1.0)
grammar.add_rule('STATE', '%s.grasp()',         ['STATE'], 1.0)
grammar.add_rule('STATE', '%s.stack()',         ['STATE'], 1.0)
# no need for recurse_ when using a Recursive Lexicon
for f in fs:
    grammar.add_rule('STATE', 'lexicon', [q(f), 'STATE'], 1.)

grammar.add_rule('BOOL', '%s.fits(%s)', ['STATE','FIT'], 1.0)
grammar.add_rule('BOOL', '%s.exists(%s)', ['STATE','TYPE'], 1.0)
grammar.add_rule('BOOL', '%s.biggest(%s)', ['STATE','TYPE'], 1.0)

grammar.add_rule('TYPE', '"top"', None, 1.0)
grammar.add_rule('TYPE', '"bottom"', None, 1.0)
grammar.add_rule('TYPE', '"both"', None, 1.0)
grammar.add_rule('TYPE', '"unspec"', None, 1.0)

grammar.add_rule('FOR', '"base"', None, 1.0)
grammar.add_rule('FOR', '"top"', None, 1.0)

grammar.add_rule('FIT', '"loose"', None, 1.0)
grammar.add_rule('FIT', '"tight"', None, 1.0)

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
        self.hand = None
        self.base = None
        self.top = None

    def __str__(self):
        return '[%s, %s, %s, %s]'  % (self.table, self.hand, self.base, self.top)

    def choose(self,what,to_be):
        the_objs = self.all_objs()
        on_top = [obj for obj in the_objs if isinstance(obj,Cup)] + [obj.top for obj in the_objs if isinstance(obj,Stack)] 
        on_bottom = [obj for obj in the_objs if isinstance(obj,Cup)] + [obj.bottom for obj in the_objs if isinstance(obj,Stack)] 

        if   what == 'top':
            filtered_table = on_top
        elif what == 'bottom':
            filtered_table = on_bottom
        elif what == 'both':
            filtered_table = set.intersection(set(on_top),set(on_bottom))
        elif what == 'unspec':
            filtered_table = the_objs
        else: raise WorldException

        if filtered_table:
            obj = sample1(filtered_table)
        else: raise WorldException

        if to_be == 'base':
            self.base = obj
        elif to_be == 'top':
            self.top = obj
        else: raise WorldException

        return self

    def grasp(self):
        if self.top and self.top in self.table:
            if self.hand:
                self.table.add(self.hand)
                self.hand = None
            self.hand = self.top
            self.table.remove(self.top)
            self.top = None
            return self
        else:
            raise WorldException

    def stack(self):
        if (self.base and self.hand and self.base != self.hand and self.base in self.table and not self.hand in self.table):
            base_size = self.base.size if isinstance(self.base,Cup) else self.base.top.size
            top_size = self.hand.size if isinstance(self.hand,Cup) else self.hand.bottom.size
            if base_size > top_size:
                new_stack = Stack(parts=[self.base, self.hand])
                self.table.remove(self.base)
                self.hand = None
                self.base = None
                self.top = None
                self.table.add(new_stack)
                return self
            else:
                raise WorldException
        else:
            raise WorldException

    def exists(self,what):
        the_objs = self.all_objs()
        on_top = [obj for obj in the_objs if isinstance(obj,Cup)] + [obj.top for obj in the_objs if isinstance(obj,Stack)] 
        on_bottom = [obj for obj in the_objs if isinstance(obj,Cup)] + [obj.bottom for obj in the_objs if isinstance(obj,Stack)] 

        if   what == 'top':
            return len(on_top) > 0
        elif what == 'bottom':
            return len(on_bottom) > 0
        elif what == 'both':
            return len(set.intersection(set(on_bottom),set(on_top))) > 0
        elif what == 'unspec':
            return len(the_objs) > 0
        else: raise WorldException

    def fits(self,how):
        if self.base and self.top and self.base != self.top:
            base_size = self.base.size if isinstance(self.base,Cup) else self.base.top.size
            top_size = self.top.size if isinstance(self.top,Cup) else self.top.bottom.size
            if how == 'tight':
                return base_size == (top_size+1)
            elif how == 'loose':
                return base_size > top_size
            else: raise WorldException
        else: raise WorldException

    def biggest(self,which):
	if which == 'top':
            return self.top == max([x.size for x in self.all_cups(self.all_objs())])
        elif which == 'base':
            return self.base == max([x.size for x in self.all_cups(self.all_objs())])
        else: raise WorldException

    def all_objs(self):
        all_objs = copy(self.table)
        if self.hand:
            all_objs.add(copy(self.hand))
        return all_objs

    def all_cups(self,the_objs):
        cups = []
	for obj in the_objs:
            if isinstance(obj,Cup):
                cups += [obj]
            else:
                cups += self.all_cups(obj.parts)
	return cups

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Hypothesis
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from math import log
from LOTlib.Miscellaneous import Infinity, attrmem, logsumexp
from LOTlib.Hypotheses.Lexicon.RecursiveLexicon import RecursiveLexicon
from LOTlib.Hypotheses.LOTHypothesis import LOTHypothesis
from LOTlib.Eval import TooBigException, RecursionDepthException

class StackerLikelihood(object):
    """ This is a neat likelihood. It favors all stacks that exist, but
    particularly the tall ones. If you have 10 cups, for example, it will favor
    a stack of 2 and 8 other cups over 10 separate cups. It will also favor 
    having 2 stacks of 2 and 6 cups overs 1 stack of 2 and 8 cups. It favors 10
    stacked cups most of all."""
    @attrmem('likelihood')
    def compute_likelihood(self, data, shortcut=None):
        assert len(data) == 0

        nTrials = 5
        ll = []
	for x in range(nTrials):
            try:
		ws = WorldState()
                ws2 = self('f0',ws)
                ll += [sum([ sum(range((o.height if isinstance(o,Stack) else 1)+1)) for o in ws2.table ])]
            except (TooBigException, RecursionDepthException, WorldException):
                ll += [-Infinity]
        return logsumexp(ll) - log(nTrials)

class StackerLexicon(StackerLikelihood,RecursiveLexicon):
    pass

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Sampling
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":

    from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
    from LOTlib import break_ctrlc,SIG_INTERRUPTED
    from LOTlib.Inference.Samplers.StandardSample import standard_sample
    from LOTlib.MPI.MPI_map import MPI_unorderedmap, is_master_process
    import itertools
    import numpy
    from LOTlib.TopN import TopN
    
    def run(make_hypothesis, make_data):
        if SIG_INTERRUPTED:
            return set()
    
        topCount = 500
        steps = 400000
	skip = 20
        return standard_sample(make_hypothesis,
                               make_data,
                               N=topCount,
                               steps=steps,
			       skip=skip,
                               show=False,
                               save_top=None,
                               prior_temperature=1.0,
                               likelihood_temperature=0.001)
    
    def make_hypothesis(**kwargs):
    
        h = StackerLexicon(propose_p=0.2,**kwargs)
    
        for f in fs:
            h.set_word(f, LOTHypothesis(grammar, display='lambda lexicon, s: %s'))
    
        return h
        
    def make_data():
        return []
    
    if True:
        seen = set()
        for h in break_ctrlc(MHSampler(make_hypothesis(),
                                       make_data(),
                                       steps=1000,
                                       skip=50,
                                       prior_temperature=1.0,
                                       likelihood_temperature=0.001)): # low temp favors higher likelihood
	    seen.add(h)
        import pickle
        with open('/home/rule/libraries/LOTlib/LOTlib/Projects/CupStacking/test2.pkl', 'w') as f:
            pickle.dump(seen, f)
#            print
#            try:
#                print h('f0',WorldState())
#            except (TooBigException, RecursionDepthException, WorldException):
#                print 'failed execution'
#            print h.posterior_score, h.prior, h.likelihood, q(h)
    else:
        # choose the appropriate map function
        nChains = 10
        args = list(itertools.product([make_hypothesis],[make_data] * nChains) )
        
        all_runs = []
        # seen = TopN(N=50,key='likelihood')
        for fs in MPI_unorderedmap(run, numpy.random.permutation(args)):
            assert is_master_process()
            print "another one bites the dust!"
        
            seen = set()
            for h in fs:
	        seen.add(h)
            all_runs += [seen]
        
        import pickle
        with open('/home/rule/libraries/LOTlib/LOTlib/Projects/CupStacking/test2.pkl', 'w') as f:
            pickle.dump(all_runs, f)

