# Often, different strategies p_i have the same necessary 
# conditions. So identify groups of same-condition strategies and 
# use Boolean minimisation to find a compact description of all the 
# p_i in each group. Thus, we summarise the SPNEs for each q.

import os
from pathlib import Path
import math
import pandas as pd
import csv
import itertools as it

from z3 import Reals, And

import fncs_z3_1 as fncs_z3
import fncs_pyeda_1 as fncs_pyeda


# ---
# parameters
# ---

# where results are stored
results_dir = Path(os.environ.get("RESULTS"))
fname_in_prefix = "necess_condns_"

# where to save results
fname_out_prefix = "necess_condns_grouped_"

# parameters that define the model
pars = {
    "all_acts": ["CC", "CD", "DC", "DD"],
    "all_envs": ["g", "b"],
}

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


# ---
# group strategies with the same necessary conditions
# ---

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
    df.set_index("p", inplace=True)

    # go through each potential SPNE and group them if their 
    # necessary conditions are equivalent
    groupedD = dict()
    for pstring in df.index:
        row = df.loc[pstring]

        # only include if it is possible to satisfy
        if not row["simultaneously_satisfiable?"]:
            continue

        # check if there are any additional conditions
        necess_exprs_piped = row["necessary_conditions"]
        if type(necess_exprs_piped) is not str:

            # no additional conditions
            assert(math.isnan(necess_exprs_piped))
            key = (0,)

            # ready a space for it
            if key not in groupedD:
                groupedD[key] = {
                    "necessary_conditions": "",
                    "necessary_conditions_xy": "",
                    "ps": set()
                }

        else:

            # additional conditions written as strings
            necess_expr_strings = sorted(necess_exprs_piped.split(" | "))
            nbr_exprs = len(necess_expr_strings)

            # convert to a tuple of expressions
            exprs = tuple([eval(necess_expr_string) for necess_expr_string in necess_expr_strings])

            # append its strategy p to the dictionary

            # are those expressions already a key in the dictionary?
            existing_keys = list(groupedD.keys())
            if not existing_keys:
                key = exprs
                groupedD[key] = {
                    "necessary_conditions": row["necessary_conditions"],
                    "necessary_conditions_xy": row["necessary_conditions_xy"],
                    "ps": set()
                }
            else:
                (is_in_list, match_idx) = fncs_z3.exprs_in_list(exprs, existing_keys)
                if is_in_list:
                    key = existing_keys[match_idx]
                else:
                    key = exprs
                    groupedD[key] = {
                        "necessary_conditions": row["necessary_conditions"],
                        "necessary_conditions_xy": row["necessary_conditions_xy"],
                        "ps": set()
                    }
        
        # append this pstring to the dictionary at the appropriate key
        groupedD[key]["ps"].add(pstring[1:])


    # use Boolean minimisation to get a compact description of all strategies in group
    # ---

    # this convert the sets of pstrings into a set of compact 
    # description where "-" indicates either response (C or D) in 
    # that state
    for key, D in groupedD.items():
        groupedD[key]["compact_ps"] = fncs_pyeda.minimise_pstrings(D["ps"])


    # write results for this q to CSV
    # ---

    # list of dictionaries form for easier export
    #  - pipe-separate each compact p 
    #  - put leading "_" so spreadsheet software doesn't get confused
    outputL = [
        {
            "necessary_conditions": D["necessary_conditions"],
            "necessary_conditions_xy": D["necessary_conditions_xy"],
            "compact_ps": " | ".join(["_" + ps for ps in D["compact_ps"]])
        }
        for exprs, D in groupedD.items()
    ]


    # write rows to csv
    df = pd.DataFrame(outputL)
    df.index.name = "id"
    fname_out = f"{fname_out_prefix}{qstring}.csv"
    file_path = results_dir / fname_out
    df.to_csv(file_path, index=True, quoting=csv.QUOTE_ALL)