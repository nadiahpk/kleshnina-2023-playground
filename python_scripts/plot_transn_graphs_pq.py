# Create dotty files to plot transition graphs for environment q and outcomes p

import os
from pathlib import Path
import subprocess # to run dot command in transn_graphs result dir
import itertools as it
import fncs_general as mf
import networkx as nx
import pandas as pd

# ---
# parameters
# ---

# where results are stored
results_dir = Path(os.environ.get("RESULTS"))
fname_in_prefix = "necess_condns_grouped_"

# where results are saved
results_dir_out = results_dir / "transn_graphs"

pars = {
    "all_acts": ["CC", "CD", "DC", "DD"],
    "all_envs": ["g", "b"],
}

# colour strings for each strategy outcome
# https://personal.sron.nl/~pault/ vibrant scheme
colours = {
    "CC": '"#009988"',
    "CD": '"#33bbee"',
    "DC": '"#33bbee"',
    "DD": '"#ee7733"',
    "bad": '"#ee3377"', 
}


# ---
# create graphs
# ---

# preamble to dotty file
preamble = '''
digraph {
    graph [rankdir=TD];
    node [style=filled];
    edge [penwidth=2];

'''
preamble += f'    gCC [label="CC", fillcolor={colours["CC"]}, shape="circle"];\n'
preamble += f'    gCD [label="CD", fillcolor={colours["CD"]}, shape="circle"];\n'
preamble += f'    gDC [label="DC", fillcolor={colours["DC"]}, shape="circle"];\n'
preamble += f'    gDD [label="DD", fillcolor={colours["DD"]}, shape="circle"];\n'
preamble += '\n'
preamble += f'    bCC [label="CC", fillcolor={colours["CC"]}, shape="doublecircle", color={colours["bad"]}, penwidth=2];\n'
preamble += f'    bCD [label="CD", fillcolor={colours["CD"]}, shape="doublecircle", color={colours["bad"]}, penwidth=2];\n'
preamble += f'    bDC [label="DC", fillcolor={colours["DC"]}, shape="doublecircle", color={colours["bad"]}, penwidth=2];\n'
preamble += f'    bDD [label="DD", fillcolor={colours["DD"]}, shape="doublecircle", color={colours["bad"]}, penwidth=2];\n'
preamble += '\n'

# ---
# for each q, for each p-group, plot range where ps are SPNE
# ---

# generate the needed q sequences
q_sequences = [
    [1, v[0], 0, 1] + list(v[1:]) for v in it.product([0, 1], repeat=3)
]
for q_sequence in q_sequences:
    print(f"Doing q = {q_sequence}")

    # into proper q vector for `create_nx_graph()`
    pars["q"] = [q_sequence[:3], q_sequence[3:]]

    # get a dataframe of the conditions on potential SPNE
    qstring = "q_" + "".join(str(v) for v in q_sequence)
    fname_in = f"{fname_in_prefix}{qstring}.csv"
    file_path = results_dir / fname_in
    df = pd.read_csv(file_path)
    df.set_index("id", inplace=True)

    # for each group of same-condition ps
    for group_idx in df.index:
        print(f"Doing id = {group_idx}")
        row = df.loc[group_idx]
        
        # get a list of p strings in their compact form
        compact_ps_piped = row["compact_ps"]
        compact_ps = compact_ps_piped.split(" | ")
        compact_ps = [compact_p[1:] for compact_p in compact_ps] # rem leading "_"
        nbr_compact_ps = len(compact_ps)

        # create a plot for each compact p (idx_p_ID)
        # ---

        for p_idx, compact_p in enumerate(compact_ps):
            dot_text = preamble

            # create list of all possible pstrs corresponding to compact_p
            if "-" not in compact_p:
                pstrs = [compact_p]
            else:
                # where each indifferent strategy is in p
                dash_idxs = [i for i, v in enumerate(compact_p) if v == "-"]
                pstrs = list()
                for poss_dashs in it.product("01", repeat=len(dash_idxs)):
                    new_pstrV = [c for c in compact_p]
                    for i, c in zip(dash_idxs, poss_dashs):
                        new_pstrV[i] = c
                    pstrs.append("".join(new_pstrV))

            # for each pstr, create network graph
            graphs = list()
            for pstr in pstrs:

                pars["p"] = [
                    ["-" if pi == "-" else int(pi) for pi in pstr[:4]],
                    ["-" if pi == "-" else int(pi) for pi in pstr[4:]],
                ]
                graphs.append(mf.create_nx_graph(pars))

            # merge the network graphs
            G = nx.DiGraph()
            for graph in graphs:
                G.add_edges_from(graph.edges())

            # write each edge to the dotty file
            for edge in G.edges():
                dot_text += f"    {edge[0]} -> {edge[1]};\n"

            # end the dotty commands
            dot_text += "}"

            # create the graph
            # ---

            # write dotty file
            qstr = "".join(str(v) for v in q_sequence)
            fname_prefix_out = f"q_{qstr}_id_{group_idx}_p_{p_idx}"
            fname_out = f"{fname_prefix_out}.dot"
            file_path = results_dir_out / fname_out
            with open(file_path, "w") as file:
                file.write(dot_text)

            # execute dot command on the dot file to produce pdf of the graph
            cmd = f"dot -Tpdf {fname_prefix_out}.dot > {fname_prefix_out}.pdf"
            subprocess.run(cmd, shell=True, cwd=results_dir_out)