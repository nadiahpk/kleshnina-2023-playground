# Written for SageMath version 9.5
#
# Before loading this in Sage, you need to do 3 things:
# 1. Load define_variables_assumptions.sage
# 2. Define boolean break_on_not_satisfied
# 3. Define longterm_payoffs dictionary with structure:
#    {state_1: {'no_deviation': symbolic_expr, 'deviation': symbolic_expr},
#     state_2: {'no_deviation': symbolic_expr, 'deviation': symbolic_expr}, ...}
#    where symbolic_expr only contains terms from define_variables_assumptions.sage

# storage
outcomes = {
    state: {
        "satisfied?": None,
        "how_determined?": None,
        "required_non_negative": None,
    }
    for state in longterm_payoffs.keys()
}

for state, payoffs in longterm_payoffs.items():

    # rewrite payoffs in (x, y) parameter space, easier for Sage
    nodev = payoffs["no_deviation"].subs(xy_subs)
    dev = payoffs["deviation"].subs(xy_subs)


    # check SPNE condition directly
    # ---

    # the condition required for SPNE is that every diff = nodev - dev >= 0
    diff = nodev - dev
    diff_gteq0 = bool(diff >= 0)
    diff_not_gteq0 = bool(diff < 0)

    if diff_gteq0 or diff_not_gteq0:
        # print(f" nodev_pay - dev_pay >= 0? {diff_gteq0}")
        outcomes[state]["satisfied?"] = diff_gteq0
        outcomes[state]["how_determined?"] = "directly"
        outcomes[state]["required_non_negative"] = diff.subs(reverse_xy_subs)

        if (not diff_gteq0) and break_on_not_satisfied:
            # if one required condition not satisfied, not SPNE
            # leave remainder as Nones
            break

        continue

    # if both evaluated False, we couldn't immediately tell, pull it apart to look closer

    # simplify further and check
    # ---

    numer, denom = diff.numerator_denominator()
    assert(not bool(denom == 0))
    denom_gt0 = bool(denom > 0)
    denom_not_gt0 = bool(denom < 0)

    # I don't think it's possible for the denominator to be ambiguous
    assert(denom_gt0 or denom_not_gt0)

    # if the denominator is negative, the required condition for the sign of the numerator flips
    if denom_not_gt0:
        numer = -numer
    
    assert(not bool(numer == 0))
    numer_gt0 = bool(numer > 0)
    numer_not_gt0 = bool(numer < 0)

    # if both evaluate False, it means Sage can't tell yet
    if numer_gt0 or numer_not_gt0:
        outcomes[state]["satisfied?"] = numer_gt0
        outcomes[state]["how_determined?"] = "normalised"
        outcomes[state]["required_non_negative"] = numer.subs(reverse_xy_subs)

        if (not numer_gt0) and break_on_not_satisfied:
            # if one required condition not satisfied, not SPNE
            # leave remainder as Nones
            break

        continue

    # if we get this far, our last alternative is to simplify with d=1

    # simplify by setting delta = 1
    # ---

    outcomes[state]["how_determined?"] = "delta = 1"

    simp_numer = numer.subs({d: 1})
    simp_numer_gteq0 = bool(simp_numer >= 0)
    simp_numer_not_gteq0 = bool(simp_numer < 0)

    # condition required is that this term is non-negative
    outcomes[state]["required_non_negative"] = simp_numer.subs(reverse_xy_subs)

    # if one evaluated true, we can tell if it's satisfied
    if simp_numer_gteq0 or simp_numer_not_gteq0:
        outcomes[state]["satisfied?"] = simp_numer_gteq0
        # otherwise leave empty, we can't tell

        if (not simp_numer_gteq0) and break_on_not_satisfied:
            # if one required condition not satisfied, not SPNE
            # leave remainder as Nones
            break


# turn the outcomes dictionary into a pipe-separated string
# ---

result_string = prepare_sage_output(outcomes)
print(result_string)