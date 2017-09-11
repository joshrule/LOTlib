class ProposalFailedException(Exception):
    """Raise when a proposer fails to generate a proposal"""
    pass


class Proposer(object):
    """
    generic Proposer class

    Assumes:
      propose_value(v): a function, giving a newly proposed value v' from v
      give_proposal_log_p(v,v'): a function, gives the probability of
          proposing v' from v
    """
    def propose(self, ret='both', newVal=None, **kwargs):
        """generate a proposal and compute its probability"""
        while newVal is None:
            try:
                newVal = self.propose_value(self.value, **kwargs)
            except ProposalFailedException:
                pass

        hypothesis = self.__copy__(value=newVal)

        # the return value depends on 'ret'
        if ret == 'value':
            return hypothesis
        else:
            logp = self.give_proposal_log_p(self.value, newVal, **kwargs)
            if ret == 'logp':
                return logp
            else:
                fb = logp - \
                     self.give_proposal_log_p(newVal, self.value, **kwargs)
                if ret == 'fb':
                    return fb
                elif ret == 'both':
                    return hypothesis, fb
                else:
                    return fb, hypothesis, logp
