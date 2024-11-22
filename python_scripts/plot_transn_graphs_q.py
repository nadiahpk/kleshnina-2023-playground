# Create dotty files to plot transition graphs for environment 
# transitions q

import os
from pathlib import Path
import subprocess # to run dot command in transn_graphs result dir
import itertools as it

# ---
# parameters
# ---

# where results are stored
results_dir = Path(os.environ.get("RESULTS"))
results_dir = results_dir / "transn_graphs"

# colour strings for each strategy outcome
# https://personal.sron.nl/~pault/ vibrant scheme
colours = {
    "CC": '"#009988"',
    "CD": '"#33bbee"',
    "DD": '"#ee7733"',
}


# ---
# create graphs
# ---

# preamble to dotty file
preamble = '''
digraph {
    graph [rankdir=LR];
    edge [penwidth=4, minlen=2];

    good [label="good", shape="circle"];
    bad [label="bad", shape="doublecircle", color="#ee3377", penwidth=2];

'''

# order of outcomes in q
outcomes = ["CC", "CD", "DD"]

# dictionary of meaning of q entries
i2env = {0: "bad", 1: "good"}

# generate the needed q sequences
q_sequences = [
    [1, v[0], 0, 1] + list(v[1:]) for v in it.product([0, 1], repeat=3)
]

for q_sequence in q_sequences:
    dot_text = preamble

    # transitions from good environment to other
    env_from = "good"
    for i in range(3):
        qi = q_sequence[i]
        dot_text += f"    {env_from} -> {i2env[qi]} [color={colours[outcomes[i]]}];\n"

    # transitions from bad environment to other
    env_from = "bad"
    for i in range(3):
        qi = q_sequence[3+i]
        dot_text += f"    {env_from} -> {i2env[qi]} [color={colours[outcomes[i]]}];\n"

    # end the dotty commands
    dot_text +="}"

    # create the graph
    # ---

    # write dotty file
    qstring = "q_" + "".join(str(v) for v in q_sequence)
    fname_out = f"{qstring}.dot"
    file_path = results_dir / fname_out
    with open(file_path, "w") as file:
        file.write(dot_text)

    # execute dot command on the dot file to produce pdf of the graph
    cmd = f"dot -Tpdf {qstring}.dot > {qstring}.pdf"
    subprocess.run(cmd, shell=True, cwd=results_dir)