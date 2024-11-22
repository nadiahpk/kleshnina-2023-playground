import networkx as nx
import json

def parse_sage_output(json_str):
    """
    Parse the JSON string returned by check_spne.sage
    back into a Python dictionary.
    
    Args:
        json_str: JSON string from Sage
        
    Returns:
        Dictionary with the original structure
    """

    data = json.loads(json_str)
    
    def process_value(value):
        if value == 'None':
            return None
        elif value == "True":
            return True
        elif value == "False":
            return False
        else:
            return value

    # process the nested dictionary
    res = {
        state: {
            key: process_value(value)
            for key, value in state_data.items()
        }
        for state, state_data in data.items()
    }

    return res


def calc_longterm_payoffs(pars, G, d, cycles, state_2_path):

    # unpack
    all_envs = pars["all_envs"]
    all_acts = pars["all_acts"]
    raw_payoffs = pars["raw_payoffs"]

    # payoff at each transient and for each cycle state
    # ---

    cycle_state_2_len = {state: len(cycle) for cycle in cycles for state in cycle}

    delta_payoffs = dict()
    all_states = [e + a for e in all_envs for a in all_acts]
    for state in all_states:
        if state not in cycle_state_2_len.keys():
            # if state is transient, payoff equal to visiting once
            delta_payoffs[state] = raw_payoffs[state]
        else:
            # if state is in a cycle, sum the payoff from each state in the
            # cycle discounted by delta
            next_state = state
            delta_payoff = raw_payoffs[next_state]
            cycle_len = cycle_state_2_len[state]
            for idx in range(1, cycle_len):
                next_state = next(G.successors(next_state))
                delta_payoff += d**idx * raw_payoffs[next_state]
            # store the sum
            delta_payoffs[state] = delta_payoff / (1 - d**cycle_len)

    # calculate the no-deviation and deviation payoffs
    # ---

    # {start_state: {"no_deviation": no_dev_payoff, "deviation": deviation_payoff}}
    longterm_payoffs = dict()

    for state in all_states:
        longterm_payoffs[state] = dict()

        # no-deviation payoff

        # this calculation does not include the initial state,
        # only the path
        path = state_2_path[state]
        longterm_payoffs[state]["no_deviation"] = sum(
            d ** (i) * delta_payoffs[state] for i, state in enumerate(path)
        )

        # deviation payoff

        # get natural next state and flip focal's strategy
        natural_next_state = next(G.successors(state))
        deviant_focal_strat = "C" if natural_next_state[1] == "D" else "D"
        next_state = natural_next_state[0] + deviant_focal_strat + natural_next_state[2]

        # make the calculation, which includes the deviated state
        path = state_2_path[next_state]
        longterm_payoffs[state]["deviation"] = delta_payoffs[next_state] + sum(
            d ** (i + 1) * delta_payoffs[state] for i, state in enumerate(path)
        )

    return longterm_payoffs


def find_path_to_cycle(pars, G, cycles):
    # find the path from every state to a cycle
    
    # unpack
    all_envs = pars["all_envs"]
    all_acts = pars["all_acts"]

    cycle_states = [state for cycle in cycles for state in cycle]
    all_states = [e + a for e in all_envs for a in all_acts]
    state_2_path = {state: list() for state in all_states}
    for state in all_states:
        # append next state
        next_state = next(G.successors(state))
        state_2_path[state].append(next_state)

        # append each next state until we reach a cycle
        while next_state not in cycle_states:
            next_state = next(G.successors(next_state))
            state_2_path[state].append(next_state)

    return state_2_path


def find_cycles(G):

    # find the attractors using the strongly-connected components algorithm
    sccs = list(nx.strongly_connected_components(G))
    cycles = []
    for scc in sccs:
        if len(scc) > 1:
            # multi-node SCCs are always cycles
            cycles.append(scc)
        elif len(scc) == 1:
            node = list(scc)[0]
            # an SCC of size 1 is an attractor iff it's a self-loop
            if G.has_edge(node, node):
                cycles.append({node})

    return cycles



def dottify_state_space_noclust(G, q=None, p=None):

    # preamble to dot file
    dot_txt = "digraph {\n\tgraph [rankdir=TD];\n\tnode [shape=circle, style=filled];\n"

    # label graph with the transition parameters if given
    if q is not None and p is not None:
        if q is not None:
            qstring = "q = (" + "; ".join([", ".join([str(q) for q in qs]) for qs in q]) + ")"
        else:
            qstring = ""
        if p is not None:
            pstring = "p = (" + "; ".join([", ".join([str(p) for p in ps]) for ps in p]) + ")"
        else:
            pstring = ""
        dot_txt += f"\tlabel=\"{qstring}\\n{pstring}\"\n\n"

    # define state nodes and environment clusters
    dot_txt +="\t{\n\t\tgCC [label=\"CC\", fillcolor=\"#ccddaa\"];\n\t\tgCD [label=\"CD\", fillcolor=\"#bbccee\"];\n\t\tgDC [label=\"DC\", fillcolor=\"#bbccee\"];\n\t\tgDD [label=\"DD\", fillcolor=\"#ffcccc\"];\n\t}\n\n\t{\n\t\tbCC [label=\"CC\", color=\"red\", shape=\"doublecircle\", style=\"filled\", fillcolor=\"#ccddaa\"];\n\t\tbCD [label=\"CD\", color=\"red\", shape=\"doublecircle\", style=\"filled\", fillcolor=\"#bbccee\"];\n\t\tbDC [label=\"DC\", color=\"red\", shape=\"doublecircle\", style=\"filled\", fillcolor=\"#bbccee\"];\n\t\tbDD [label=\"DD\", color=\"red\", shape=\"doublecircle\", style=\"filled\", fillcolor=\"#ffcccc\"];\n\t}\n\n"

    # actual graph structure
    for edge in G.edges():
        dot_txt += f"\t{edge[0]} -> {edge[1]};\n"
    dot_txt += "}"

    return dot_txt


def dottify_state_space(G, q=None, p=None):

    # preamble to dot file
    dot_txt = "digraph {\n\tgraph [rankdir=TD];\n\tnode [shape=circle, style=filled];\n"

    # label graph with the transition parameters if given
    if q is not None and p is not None:
        qstring = "q = (" + "; ".join([", ".join([str(q) for q in qs]) for qs in q]) + ")"
        pstring = "p = (" + "; ".join([", ".join([str(p) for p in ps]) for ps in p]) + ")"
        dot_txt += f"\tlabel=\"{qstring}\\n{pstring}\"\n\n"

    # define state nodes and environment clusters
    dot_txt +="\tsubgraph cluster_good {\n\t\tlabel=\"good\"\n\t\tstyle=\"filled\"\n\t\tfillcolor=\"#cceeff\"\n\t\tgCC [label=\"CC\", fillcolor=\"#ccddaa\"];\n\t\tgCD [label=\"CD\", fillcolor=\"#bbccee\"];\n\t\tgDC [label=\"DC\", fillcolor=\"#bbccee\"];\n\t\tgDD [label=\"DD\", fillcolor=\"#ffcccc\"];\n\t}\n\n\tsubgraph cluster_bad {\n\t\tlabel=\"bad\"\n\t\tstyle=\"filled\"\n\t\tfillcolor=\"#eeeebb\"\n\t\tbCC [label=\"CC\", fillcolor=\"#ccddaa\"];\n\t\tbCD [label=\"CD\", fillcolor=\"#bbccee\"];\n\t\tbDC [label=\"DC\", fillcolor=\"#bbccee\"];\n\t\tbDD [label=\"DD\", fillcolor=\"#ffcccc\"];\n\t}\n\n"

    # actual graph structure
    for edge in G.edges():
        dot_txt += f"\t{edge[0]} -> {edge[1]};\n"
    dot_txt += "}"

    return dot_txt


def determine_next_outcome(q, p, last_env, last_act):
    """
    Inputs
    ---

    q, list of lists of 0,1
        Probability of environment to transition to "good" state 
        given previous state and actions. Same format as in 
        Kleshnina et al. (2023), i.e.,
                  CC, CD/DC,    DD
            q = [[ 1,     0,     0], good env
                 [ 1,     1,     1]] bad env

    p, list of lists of 0,1
        Probability of focal player to play "cooperate" given
        *current* environmental state and previous actions. Same 
        format as in Kleshnina et al. (2023), i.e.,
                 CC, CD, DC, DD
            p = [[1,  0,  0,  0], good env
                 [1,  0,  0,  1]] bad env

    last_env, str
        The last environment. Either "g" for "good" or "b" for 
        "bad" environment.

    last_act, str
        The last actions of players, e.g., "CC" for both cooperated
        and "CD" for Player 1 cooperated and Player 2 defected

    Outputs
    ---

    outcome, tuple of strings (next_env, next_act)
        The next environment and next action in same format as inputs
        last_env and last_act above.

    """
    
    # p = [[1, 0, 0, 0], [1, 0, 0, 1]]

    # by definition::
    env_row = {"g": 0, "b": 1}
    q_col = {"CC": 0, "CD": 1, "DC": 1, "DD": 2}
    p_col = {"CC": 0, "CD": 1, "DC": 2, "DD": 3}

    # next environment is a function of last env and both 
    # players' acts
    row = env_row[last_env]
    col = q_col[last_act]
    next_env = "g" if q[row][col] == 1 else "b"

    # next actions are a function of *current* environment
    # (which is here "next_env") and players' last acts
    row = env_row[next_env]

    # player 1 and 2
    col1 = p_col[last_act]
    next_act1 = "C" if p[row][col1] == 1 else "D"
    col2 = p_col[last_act[::-1]] # reverses so player 2 now focal
    next_act2 = "C" if p[row][col2] == 1 else "D"
    next_act = next_act1 + next_act2

    # the total outcome
    outcome = (next_env, next_act)

    return outcome

def create_nx_graph(pars):
    
    # unpack
    q = pars["q"]
    p = pars["p"]
    all_envs = pars["all_envs"]
    all_acts = pars["all_acts"]

    # find every next step
    all_outs = [(e, a) for e in all_envs for a in all_acts]
    all_next = [
        determine_next_outcome(q, p, last_env, last_act)
        for last_env, last_act in all_outs
    ]

    # turn into graph
    edges = [
        ("".join(init_tuple), "".join(next_tuple))
        for init_tuple, next_tuple in zip(all_outs, all_next)
    ]
    G = nx.DiGraph()
    G.add_edges_from(edges)

    return G
