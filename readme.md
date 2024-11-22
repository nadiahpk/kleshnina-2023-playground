# About this code 

I wrote this code to teach myself the methods used in 
Kleshnina, M., et al. 2023. The effect of environmental information 
on evolution of cooperation in stochastic games. *Nature Communications*, 14(1):4153.
I wrote a blog post about [here](https://nadiah.org/2024/11/20/kleshnina_2023).

In Supplementary 3, 
Kleshnina explains how to check if a strategy is a subgame perfect Nash equilibrium (SPNE), 
or has the potential to be one. 
In the latter case, 
she shows how and to find the necessary conditions on the parameter values.

The purpose of this code is to automate those checks.
I used a combination of:
- SymPy symbolic maths library
- SageMath open-source math software built on Python
- Z3 theorem proving library
- PyEDA Boolean minimisation

In the `results` directory, I've only included the results for the timeout-grim-wsls
scenario to be polite to Github,
but the scripts will generate the whole set of scenarios described in the blog post.

# How to run it

1. `calc_one_shot_devns.py` uses SageMath to check 
$\pi_{s} - \tilde{\pi}_{s} \geq 0$ (e.g., Eqns. 26-28 in Supp 3).
Mostly, this rules out strategies that can never be SPNEs.
    1. Navigate to directory `sage_scripts`
    2. Start a Sage Jupyter Notebook server
        1. `eval "$(/home/USERNAME/miniforge3/bin/conda shell.bash hook)"`
        2. `conda activate sage`
        3. `JUPYTER_TOKEN=253184f458c7ca7a924ef86a600ba76529fdd2665e8e81c5 sage -n jupyter --port 8888 --no-browser --ip=0.0.0.0`
    3. Leave that running in that terminal
    4. Navigate to directory `python_scripts`
    5. Start ipython
    6. `%run calc_one_shot_devns.py`

2. `calc_necess_condns.py` Given the one-shot deviation payoff differences, 
for every strategy with the potential to be SPNE, 
identify which of the conditions are necessary (if any).

3. `group_necess_condns.py` Identify groups of same-conditions strategies and 
use Boolean minimisation to find a compact description of all the $\boldsymbol{p}$ in each group. 

4. `plot_necess_condns.py` Plot in $(x, y)$ space the region where the strategies are a SPNE.
