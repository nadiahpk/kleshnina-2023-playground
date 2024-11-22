# Written for SageMath version 9.5
#
# Run this before defining longterm_payoffs dictionary
# and running check_spne.sage

import json

def prepare_sage_output(outcomes_dict):
    """
    Convert a dictionary of outcomes to a JSON string that can be safely passed from Sage.
    
    Args:
        outcomes_dict: Dictionary with the structure of the outcomes
        
    Returns:
        JSON string representation of the dictionary
    """

    def sage_to_python(value):
        if value is None:
            return None
        return str(value)
    
    # Process the nested dictionary
    processed_dict = {
        str(state): {
            key: sage_to_python(value)
            for key, value in state_data.items()
        }
        for state, state_data in outcomes_dict.items()
    }
    
    # Convert to JSON string
    return json.dumps(processed_dict)

# ==============================

# variables
forget() # clear previous
b1, b2, c, d = var('b1, b2, c, d')

# assumptions rewritten for Sage
assume(d > 0) # 0 < d <= 1
assume(d < 1)
assume(c > 0)
x, y = var("x, y") # x = b2 - c; y = b1 - b2
assume(x > 0) # b1 ≥ b2 > c
assume(y > 0) # NOTE changing this to make more sense

# (x, y) parameter space easier for Sage
xy_subs = {b2: c + x, b1: c + x + y}
reverse_xy_subs = {x: b2 - c, y: b1 - b2}
