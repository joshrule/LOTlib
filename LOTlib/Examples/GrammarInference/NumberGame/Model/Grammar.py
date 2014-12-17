
from LOTlib.Grammar import Grammar


# ------------------------------------------------------------------------------------------------------------
simple_test_grammar = Grammar()
simple_test_grammar.add_rule('START', '', ['SET'], 1.)

# Mapping expressions over sets of numbers
simple_test_grammar.add_rule('SET', 'mapset_', ['FUNC', 'RANGE'], 1.)
simple_test_grammar.add_rule('RANGE', 'range_set_', ['1', '20', 'bound=20'], 1.)
simple_test_grammar.add_rule('FUNC', 'lambda', ['EXPR'], 1., bv_type='X', bv_p=1.)

# Expressions
simple_test_grammar.add_rule('EXPR', 'times_', ['X', '1'], 1.)
simple_test_grammar.add_rule('EXPR', 'times_', ['X', '2'], 1.)
simple_test_grammar.add_rule('EXPR', 'times_', ['X', '3'], 1.)
simple_test_grammar.add_rule('EXPR', 'times_', ['X', '7'], 1.)


# ------------------------------------------------------------------------------------------------------------
simple_grammar_2 = Grammar()
simple_grammar_2.add_rule('START', '', ['SET'], 1.)

# Mapping expressions over sets of numbers
simple_grammar_2.add_rule('SET', 'mapset_', ['FUNC', 'RANGE'], 1.)
simple_grammar_2.add_rule('RANGE', 'range_set_', ['1', '20', 'bound=20'], 1.)
simple_grammar_2.add_rule('FUNC', 'lambda', ['EXPR'], 1., bv_type='X', bv_p=1.)

# Expressions
simple_grammar_2.add_rule('EXPR', 'times_', ['X', 'CONST'], 1.)     # X * n
simple_grammar_2.add_rule('EXPR', 'ipowf_', ['X', 'CONST'], 1.)     # X ^ n
simple_grammar_2.add_rule('EXPR', 'ipowf_', ['CONST', 'X'], 1.)     # n ^ X
simple_grammar_2.add_rule('EXPR', 'plus_', ['X', 'CONST'], 1.)      # X + n

for i in range(1,6):
    simple_grammar_2.add_rule('CONST', str(i), None, 1.)


# ------------------------------------------------------------------------------------------------------------

complex_grammar = Grammar()
complex_grammar.add_rule('START', '', ['SET'], 1.)

# Mapping expressions over sets of numbers
complex_grammar.add_rule('SET', 'mapset_', ['FUNC', 'RANGE'], 1.)
complex_grammar.add_rule('RANGE', 'range_set_', ['1', '20', 'bound=20'], 1.)
complex_grammar.add_rule('FUNC', 'lambda', ['X'], 1., bv_type='X', bv_p=1.)

# Expressions
complex_grammar.add_rule('X', 'times_', ['X', 'CONST'], 1.)     # X * n
complex_grammar.add_rule('X', 'ipowf_', ['X', 'CONST'], 1.)     # X ^ n
complex_grammar.add_rule('X', 'ipowf_', ['CONST', 'X'], 1.)     # n ^ X
complex_grammar.add_rule('X', 'plus_', ['X', 'CONST'], 1.)      # X + n

for i in range(1,6):
    complex_grammar.add_rule('CONST', str(i), None, 1.)




