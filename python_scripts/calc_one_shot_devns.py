# Calculate the one-shot deviation payoff differences for every
# strategy for every q of the form
#   q = (1, -, 0; 1, -, -)
# and test if conditions required for the strategy to be a SPNE
# are never satisfied, always satisfied, or depend on conditions on
# the parameter values. In the latter case, write those conditions.

import os
import sympy as sp
import pandas as pd
import csv
import itertools as it
from pathlib import Path

import fncs_general as mf
from fncs_jupyter import JupyterClient

# ===================================================================

# ---
# parameters
# ---

# where to save results
fname_out_prefix = "one_shot_devns_"

# b_1, b_2, c, delta
b1, b2, c, d = sp.symbols("b1, b2, c, d")

pars = {
    "all_acts": ["CC", "CD", "DC", "DD"],
    "all_envs": ["g", "b"],
    # "q": q,
    # "p": p,
    "raw_payoffs": {
        "gCC": b1 - c,
        "gCD": -c,
        "gDC": b1,
        "gDD": 0,
        "bCC": b2 - c,
        "bCD": -c,
        "bDC": b2,
        "bDD": 0,
    },
}

# ---
# check SPNE condition for each environment q and strategy vector p
# ---

# To start up Jupyter client and start Sage kernel:
#
# 1. Navigate to sage_scripts
# 2. eval "$(/home/elendil/miniforge3/bin/conda shell.bash hook)"
# 3. conda activate sage
# 4. JUPYTER_TOKEN=253184f458c7ca7a924ef86a600ba76529fdd2665e8e81c5 sage -n jupyter --port 8888 --no-browser --ip=0.0.0.0

jupyter = JupyterClient(
    "http://localhost:8888", "253184f458c7ca7a924ef86a600ba76529fdd2665e8e81c5"
)

cmd = "load('define_variables_assumptions.sage')"
jupyter.execute_code(cmd)

cmd = "break_on_not_satisfied = False"
jupyter.execute_code(cmd)

# generate the needed q sequences
q_sequences = [
    [1, v[0], 0, 1] + list(v[1:]) for v in it.product([0, 1], repeat=3)
]

for q_sequence in q_sequences:
    print(f"Doing q = {q_sequence}")

    # environment transition vector
    q = [q_sequence[:3], q_sequence[3:]]
    pars["q"] = q

    # for q, check SPNE condition for each strategy vector p
    # ---

    rows = list()  # storage
    for p_sequence in it.product([0, 1], repeat=8):
        print(f" Doing p = {p_sequence}... ")

        # strategy vector
        p = [p_sequence[:4], p_sequence[4:]]
        pars["p"] = p

        # find longterm no-deviation and deviation payoffs
        # ---

        G = mf.create_nx_graph(pars)  # networkx graph of transitions
        cycles = mf.find_cycles(G)  # terminating cycles
        state_2_path = mf.find_path_to_cycle(
            pars, G, cycles
        )  # path from every state to a cycle
        longterm_payoffs = mf.calc_longterm_payoffs(pars, G, d, cycles, state_2_path)

        # use Sage Jupyter Client to check SPNE conditions
        # ---

        cmd = f"longterm_payoffs = {longterm_payoffs}"
        jupyter.execute_code(cmd)

        cmd = "load('check_spne.sage')"
        result = jupyter.execute_code(cmd)

        # if we have any "satisfied?" = False, this is not a SPNE
        # ---

        # parse result
        presult = mf.parse_sage_output(result)
        not_SPNE = any(
            [resultD["satisfied?"] == False for state, resultD in presult.items()] # noqa
        )

        # save results as a row in dataframe
        # ---

        # add strategy vector p and summary result
        row = {
            # leading undescore so spreadsheet program treats as string
            "p": "_" + "".join(["".join([str(p) for p in ps]) for ps in p]),
            "not_SPNE": not_SPNE,
        }

        # collapse results dictionary
        for state, resultsD in presult.items():
            for key, value in resultsD.items():
                row[f"{state}_{key}"] = value

        # store
        rows.append(row)

    # write result to csv
    # ---

    # construct file name for output csv
    results_dir = Path(os.environ.get("RESULTS"))
    qstring = "q_" + "".join(["".join([str(q) for q in qs]) for qs in q])
    file_name = f"{fname_out_prefix}{qstring}.csv"
    file_path = results_dir / file_name

    # write rows to csv
    df = pd.DataFrame(rows)
    df.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)


# close Jupyter Sage kernel
jupyter.close()
