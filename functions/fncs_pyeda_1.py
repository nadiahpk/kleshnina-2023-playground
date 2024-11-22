import pyeda.inter as eda

def minimise_pstrings(pstrings):
    """
    For a list of strings encoding a set of strategies p,
    e.g., pstrings = ["00000000", "00001000", "10000000", "10001000"],
    return an equivalent list where indifferent strategies are marked
    with a "-", e.g., pstrings_min = ["-000-000"]

    Uses the pyeda Boolean algebra package.
    """

    # turn the list of p strings into boolean expression
    # ---

    p_len = len(next(iter(pstrings)))  # it's 8

    # initialise 8 boolean variables to represent each of the responses
    # in a strategy p
    var_list = [f"x{i}" for i in range(1, p_len + 1)]
    bool_vars = list(map(eda.exprvar, var_list))

    # turn the p strings into a boolean expression
    andsList = list()
    for pstring in pstrings:
        boolset = set(
            xval if int(ival) else ~xval for ival, xval in zip(pstring, bool_vars)
        )
        andsList.append(eda.And(*boolset))

    bool_expr = eda.Or(*andsList)
    # e.g., Or(
    #           And(~x1, ~x2, ~x3, ~x4, ~x5, ~x6, ~x7, ~x8),
    #           And(~x1, ~x2, ~x3, ~x4, x5, ~x6, ~x7, ~x8),
    #           And(x1, ~x2, ~x3, ~x4, ~x5, ~x6, ~x7, ~x8) ...
    #       )


    # minmise the boolean expression
    # ---

    (bool_expr_min,) = eda.espresso_exprs(bool_expr)
    # e.g., Or(
    #           And(x1, x2, x3, x4, x5, x6, x7, x8),
    #           And(~x2, ~x3, ~x4, ~x6, ~x7, ~x8))
    #       )


    # convert the minimised boolean expression into a p string
    # ---

    # e.g., bool_expr_min = And(~x2, ~x3, ~x4, ~x6, ~x7, ~x8) means p
    # string '-000-000' where '-' indicates it doesn't matter if we
    # cooperate or not in this state

    # b_sets is a set of frozen sets of integers whose value is the index
    # of the variable and whose sign indicates whether var is True (+)
    # or False (-)
    b_dict, b_len, b_sets = bool_expr_min.encode_dnf()
    # e.g., {frozenset({-8, -7, -6, -4, -3, -2}), frozenset({1, 2, 3, 4, 5, 6, 7, 8})}

    # but note the indices in the frozen sets are keys to b_dict,
    # not to our original list of variables

    # create dictionary
    val_2_idx_entry = dict(zip(
        bool_vars + [~x for x in bool_vars],
        [(idx, "1") for idx in range(p_len)] + [(idx, "0") for idx in range(p_len)]
    ))


    # convert b_sets into a list of p strings with '-' for indifferent
    # strategies, our minimised p strings
    pstrings_min = set()
    for b_set in b_sets:
        
        # any that aren't in the minimised expression are indifferent
        pstring_list = ['-'] * p_len

        # for each key, find out what entry and where
        for key in b_set:
            val = b_dict[key]
            idx, entry = val_2_idx_entry[val]
            pstring_list[idx] = entry
        
        pstring = "".join(pstring_list)
        pstrings_min.add(pstring)

    return pstrings_min