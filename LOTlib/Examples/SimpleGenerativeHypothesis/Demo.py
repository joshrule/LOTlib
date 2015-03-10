# -*- coding: utf-8 -*-

"""
 A demo of "syntax" learning using a SimpleGenerativeHypothesis.

 This searches over probabilistic generating functions, running them forward to estimate
 the likelihood of the data. Very very simple.

"""
from LOTlib.Inference.Samplers.MetropolisHastings import MHSampler
from LOTlib import break_ctrlc
from LOTlib.Hypotheses.SimpleGenerativeHypothesis import SimpleGenerativeHypothesis
from Model import *

if __name__ == "__main__":

    # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    h0 = SimpleGenerativeHypothesis(grammar, args=[''] )

    ## populate the finite sample by running the sampler for this many steps
    for h in break_ctrlc(MHSampler(h0, data, 100000, skip=100)):
        print h.posterior_score, h.prior, h.likelihood, h
        print h.llcounts
