from z3 import (
    And,
    Solver,
    unsat,
    ForAll,
    Implies,
)

def exprs_in_list(expr_tuple_a, list_expr_tuples):
    """
    Returns (True, idx) if the tuple of expressions expr_tuple_a
    is in the list of tuples of expressions list_expr_tuples);
    otherwise, returns (False, None)
    """

    len_expr_tuple_a = len(expr_tuple_a)

    # initialise it by assuming it isn't
    is_in_list = False
    match_idx = None

    # for each comparison tuple in the list
    for idx, expr_tuple_b in enumerate(list_expr_tuples):

        # we can skip this comparison if the lengths don't match
        if len(expr_tuple_b) != len_expr_tuple_a:
            continue

        # if the lengths match, count how many terms match,
        nbr_matches = 0
        for expr_a, expr_b in zip(expr_tuple_a, expr_tuple_b):
            if are_equivalent(expr_a, expr_b):
                nbr_matches += 1

        # if the number of matches = the number of expressions,
        # this is a full match
        if nbr_matches == len_expr_tuple_a:
            is_in_list = True
            match_idx = idx
            break

    return(is_in_list, match_idx)



def are_equivalent(condn_a, condn_b):
    """
    Returns True if condn_a and condn_b and equivalent.
    """

    s = Solver()
    s.add(condn_a != condn_b)
    result = s.check() == unsat

    return result


def check_implication(condn_a, condn_b, assumptions, variables, tactic):
    """
    Returns True if condn_a implies condn_b under the given assumptions
    """

    formula = ForAll(variables, Implies(And(assumptions, condn_a), condn_b))
    result = tactic.apply(formula)

    return result.as_expr()
