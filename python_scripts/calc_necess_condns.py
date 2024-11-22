# Each strategy typically has a number of different conditions 
# condn_1, condn_2, etc. that must satisfied in order to be an SPNE. 
# Some conditions are sufficient for others, which makes the others 
# superfluous, e.g., a sequence condn_2 -> condn_1 -> cond_4 -> ... 
# means cond_1, cond_4, ... are superfluous, and condn_2 is the only
# necessary condition of this set. Others might have no relationships
# with the others, and they are independently necessary for the 
# strategy to be a SPNE.
#
# Given the one-shot deviation payoff differences, for every strategy
# with the potential to be SPNE, identify which of the conditions are
# necessary (if any).

import os
import math
import pandas as pd
import csv
import itertools as it
from pathlib import Path

from z3 import (
    Reals,
    And,
    simplify,
    substitute,
    Solver,
    unsat,
    Tactic,
)

import fncs_z3_1 as fncs_z3

# ===================================================================

# ---
# parameters
# ---

# where results are stored
results_dir = Path(os.environ.get("RESULTS"))
fname_in_prefix = "one_shot_devns_"

# where to save results
fname_out_prefix = "necess_condns_"

# parameters that define the model
pars = {
    "all_acts": ["CC", "CD", "DC", "DD"],
    "all_envs": ["g", "b"],
}
all_states = [e + a for e in pars["all_envs"] for a in pars["all_acts"]]

# variables and assumptions

# original parameters space
b1, b2, c, d = Reals("b1 b2 c d")
variables = [b1, b2, c, d]
assumptions = And(
    d > 0,
    d <= 1,
    c > 0,  # b1 ≥ b2 > c
    b2 > c,
    b1 > b2, # NOTE I changed this from Maria's b1 >= b2
)

# alternative parameter space
# where x = b2 - c; y = b1 - b2
x, y = Reals("x y")
b2xy = ((b2, c + x), (b1, c + x + y))  # for conversion


# ---
# find minimal conditions for potential SPNE
# ---

# method used for checking implication ordering
tactic_qe = Tactic("qe")

# generate the needed q sequences
q_sequences = [
    [1, v[0], 0, 1] + list(v[1:]) for v in it.product([0, 1], repeat=3)
]

for q_sequence in q_sequences:
    print(f"Doing q = {q_sequence}")
    q = [q_sequence[:3], q_sequence[3:]]

    # get a dataframe of the conditions on potential SPNE
    qstring = "q_" + "".join(["".join([str(q) for q in qs]) for qs in q])
    fname_in = f"{fname_in_prefix}{qstring}.csv"
    file_path = results_dir / fname_in
    df = pd.read_csv(file_path)
    df = df[~df["not_SPNE"]]
    df.set_index("p", inplace=True)

    # results for each strategy p with a potential to be SPNE 
    outputL = list() # storage
    for pstring in df.index:
        row = df.loc[pstring]

        # get each condition that we're not sure if it's satisfied
        expr_strings = [
            row[f"{state}_required_non_negative"]
            for state in all_states
            if math.isnan(row[f"{state}_satisfied?"])
        ]

        if len(expr_strings) == 0:
            # means all are known to be satisfied (all True)
            outputL.append(
                {
                    "p": pstring,
                    "simultaneously_satisfiable?": True,
                    "necessary_conditions": "",
                    "necessary_conditions_xy": "",
                }
            )
            continue

        # if we get this far, then we want to find the ordering
        # of implication on the conditions needed

        # turn the not-sure expressions into a list of expressions
        expr_full = [eval(expr) for expr in expr_strings]

        # remove from list all equivalent expressions
        exprs = []  # unique
        for expr in expr_full:
            is_unique = True
            for unique_expr in exprs:
                if fncs_z3.are_equivalent(expr, unique_expr):
                    is_unique = False
                    break
            if is_unique:
                exprs.append(expr)

        # turn the expressions into conditions (required non-negative)
        condns = [expr >= 0 for expr in exprs]

        # check conditions' mutual satisfiability
        s = Solver()
        s.add(assumptions)
        for condn in condns:
            s.add(condn)
        result = s.check()

        if result == unsat:
            # print("\n The conditions are not simultaneously satisfiable.")
            outputL.append(
                {
                    "p": pstring,
                    "simultaneously_satisfiable?": False,
                    "necessary_conditions": "",
                    "necessary_conditions_xy": "",
                }
            )
            continue

        # create an adjacency matrix of implications

        # element (row, col) is the result for condn_col -> condn_row
        # EXCEPT when row == col, then the result is the default False
        implications = [
            [
                False
                if row == col
                else fncs_z3.check_implication(
                    condn_col, condn_row, assumptions, variables, tactic_qe
                )
                for col, condn_col in enumerate(condns)
            ]
            for row, condn_row in enumerate(condns)
        ]

        # the minimal set is the set of all conditions that are not implied
        # by another conditions, i.e., independent roots of the implications
        # tree
        assert len(exprs) == len(implications)
        minimal_exprs = [
            expr
            for expr, implied_bys in zip(exprs, implications)
            if any(implied_bys) is False
        ]

        # convert into x, y parameter space
        minimal_xy_exprs = [simplify(substitute(expr, *b2xy)) for expr in minimal_exprs]

        # store
        outputL.append(
            {
                "p": pstring,
                "simultaneously_satisfiable?": True,
                "necessary_conditions": " | ".join([str(expr) for expr in minimal_exprs]),
                "necessary_conditions_xy": " | ".join(
                    [str(expr) for expr in minimal_xy_exprs]
                ),
            }
        )

    # write to CSV
    # ---

    # write rows to csv
    df = pd.DataFrame(outputL)
    fname_out = f"{fname_out_prefix}{qstring}.csv"
    file_path = results_dir / fname_out
    df.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)