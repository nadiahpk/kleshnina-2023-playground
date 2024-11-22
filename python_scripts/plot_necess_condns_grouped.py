# For each environment q, for each group of same-condition strategies
# P, plot in (x, y) space the region where the strategies are a SPNE

import os
from pathlib import Path
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import math
import itertools as it


# ---
# parameters
# ---

# where results are stored
results_dir = Path(os.environ.get("RESULTS"))
fname_in_prefix = "necess_condns_grouped_"

# where to save results (as pdf)
fname_out_prefix = "necess_condns_grouped_"

# plotting control
default_alpha = 0.6 # shading of fill region
xy_max = 3 # plot range 0 <= x, y <= xy_max (c = 1)
default_c = 1
default_delta = 1 

# work in xy space
x, y, c, d = sp.symbols("x, y, c, d")


# ---
# for each q, for each p-group, plot range where ps are SPNE
# ---

# generate the needed q sequences
q_sequences = [
    [1, v[0], 0, 1] + list(v[1:]) for v in it.product([0, 1], repeat=3)
]

for q_sequence in q_sequences:
    print(f"Doing q = {q_sequence}")

    # get a dataframe of the conditions on potential SPNE
    qstring = "q_" + "".join(str(v) for v in q_sequence)
    fname_in = f"{fname_in_prefix}{qstring}.csv"
    file_path = results_dir / fname_in
    df = pd.read_csv(file_path)
    df.set_index("id", inplace=True)

    # for each group of same-condition ps
    for idx in df.index:
        row = df.loc[idx]
        necess_conds_piped = row["necessary_conditions_xy"]

        # plot it
        fig = plt.figure(figsize=(3, 3))
        ax = plt.subplot(111)

        if type(necess_conds_piped) is not str:
            assert(math.isnan(necess_conds_piped))

            # colour the whole space
            plt.axvspan(0, xy_max, color="blue", alpha = default_alpha)

        else:

            necess_cond_strings = necess_conds_piped.split(" | ")
            nbr_condns = len(necess_cond_strings)

            for necess_cond_string in necess_cond_strings:

                condn = eval(f"{necess_cond_string} >= 0")
                condn = condn.subs({c: default_c, d: default_c})

                if y in condn.free_symbols:
                    # solve for y
                    res = sp.solve(condn, y)

                    # this will give me an infinity bound, which I don't need
                    # e.g., res.args = (y < oo, y >= 1/2 - x/2)
                    assert(len(res.args) == 2)
                    y_eqn = None
                    for res_arg in res.args:
                        if (sp.oo not in res_arg.args) and (-sp.oo not in res_arg.args):
                            y_eqn = res_arg
                    assert(y_eqn is not None)

                    # now we'll have something like y_eqn = y >= 1/2 - x/2

                    # figure out which side the function part is on
                    if y in y_eqn.lhs.free_symbols:
                        y_bound = y_eqn.rhs
                        y_side = "lhs"
                    else:
                        y_bound = y_eqn.lhs
                        y_side = "rhs"

                    # turn the bound into a function that can accept numpy arrays as arguments
                    y_fnc = sp.lambdify(x, y_bound, "numpy")

                    # for a range of x values, calculate y
                    x_vals = np.linspace(0, xy_max, 100)
                    y_vals = y_fnc(x_vals)

                    # we need to know if we're filling between y and xy_max
                    # or y and 0
                    if y_side == "lhs":
                        is_greater = y_eqn.rel_op == ">="
                    else:
                        is_greater = y_eqn.rel_op == "<="

                    # how we do the fill depends on the relation operator
                    if is_greater:
                        plt.fill_between(x_vals, y_vals, xy_max, color="blue", alpha = default_alpha / nbr_condns)
                    else:
                        plt.fill_between(x_vals, y_vals, 0, color="blue", alpha = default_alpha / nbr_condns)
                    
                else:
                    # solve for x, e.g., x <= 1
                    res = sp.solve(condn, x)

                    # find the result without the infinity bound
                    assert(len(res.args) == 2)
                    x_eqn = None
                    for res_arg in res.args:
                        if (sp.oo not in res_arg.args) and (-sp.oo not in res_arg.args):
                            x_eqn = res_arg
                    assert(x_eqn is not None)

                    # figure out which side the function part is on
                    if x in x_eqn.lhs.free_symbols:
                        x_bound = x_eqn.rhs
                        x_side = "lhs"
                    else:
                        x_bound = x_eqn.lhs
                        x_side = "rhs"

                    # we need to know if we're filling between x and xy_max
                    # or x and 0
                    if x_side == "lhs":
                        is_greater = x_eqn.rel_op == ">="
                    else:
                        is_greater = x_eqn.rel_op == "<="

                    # how we do the fill depends on the relation operator
                    if is_greater:
                        plt.axvspan(x_bound, xy_max, color="blue", alpha = default_alpha / nbr_condns)
                    else:
                        plt.axvspan(0, x_bound, color="blue", alpha = default_alpha / nbr_condns)

        # decorate the plot
        ax.axvline(default_c, color="black")
        ax.axhline(default_c, color="black")
        ax.set_xlabel(r"$x = b_2 - c$", fontsize="large")
        ax.set_ylabel(r"$y = b_1 - b_2$", fontsize="large")
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['0', '$c$'])
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['0', '$c$'])
        ax.set_xlim((0, xy_max))
        ax.set_ylim((0, xy_max))
        ax.set_aspect('equal')
        plt.tight_layout()

        # save the plot
        fname_out = f"{fname_out_prefix}{qstring}_id_{idx}.pdf"
        file_path = results_dir / fname_out
        plt.savefig(file_path)
        plt.close("all")