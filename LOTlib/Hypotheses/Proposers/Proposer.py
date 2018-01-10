class ProposalFailedException(Exception):
    """Raise when a proposer fails to generate a proposal"""
    pass


class Proposer(object):
    """
    generic Proposer class

    Assumes:
      propose_value(v): a function, giving a newly proposed value v' from v
      give_proposal_log_fb(v,v'): a function, gives the forward-backward
          probability: p(v'|v)/p(v|v')
    """
    def propose(self, **kwargs):
        """generate a proposal and compute its probability"""
        while True:
            try:
                newVal = self.propose_value(self.value, **kwargs)
                break
            except ProposalFailedException:
                pass

        hypothesis = self.__copy__(value=newVal)

        fb = self.give_proposal_log_fb(self.value, newVal, **kwargs)

        return hypothesis, fb
