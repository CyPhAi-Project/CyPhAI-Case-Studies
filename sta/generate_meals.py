from typing import List, Dict, Tuple

from sta.build_automaton import build_sa
from sta.input_generator import InputGenerator

'''
-n
30
-l
15
-o
examples/pancreas/output/traces/data_{}{}.mat
-a
examples/pancreas/output/abstract_trajectories.json
-c
examples/pancreas/output/concrete_trajectories.json
--sta
examples/pancreas/output/sta_product.prism
--dt
0.001
--wg
lib/wordgen
'''
STA_OUT_FNAME = "sta/output/sta_product.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/concrete_trajectories.json"
def generate_meals(n_scenarios: int, generator:InputGenerator=None):
    sta, volume_dict, abstraction_dict, constraints_mapping, sta_prism, sta_prism_constr, var_names, var_bounds \
        = build_sa()

    if not generator:
        sta_input_gen: InputGenerator = InputGenerator(
            sta,var_names,var_bounds,STA_OUT_FNAME,"lib/wordgen",postprocessing_fun=build_meals
        )
    else:
        sta_input_gen = generator

    scenarios = sta_input_gen.generate(6, ABSTRACT_TRAJ_FNAME,CONCRETE_TRAJ_FNAME,n=n_scenarios)
    return scenarios, sta_input_gen

def build_meals(concrete_trajectory: dict) -> List[Tuple[float, List[float]]]:
    meals: List[Tuple[float, List[float]]] = []
    meals_print = []
    times: List[float] = []
    t = 0
    m2_stored = 0
    loc = "need_breakfast"

    for meal in concrete_trajectory:
        # mock_meal = False
        d = round(meal['delay'], 2)
        m = round(meal['vars']['m'], 1)
        m1 = round(meal['vars']['m1'], 1)
        m2 = round(meal['vars']['m2'], 1)
        action = meal['action']

        if loc == "need_breakfast":
            m2_stored = 0
            if action == "to_lunch": # taking b -> l transition
                loc = "need_lunch"
                m2_stored = m2
                # add empty snack
                # mock_meal = True
            else: # action=="to_snack_1": taking b -> s1 transition
                loc = "need_snack_1"
            amount = m
            name = "Breakfast"

        elif loc == "need_snack_1":
            amount = m1
            m2_stored = m2
            loc = "need_lunch"
            name = "Snack 1"

        elif loc == "need_lunch":
            if action=="to_snack_2": # taking l -> s2 transition
                loc = "need_snack_2"

            else: # action="to_dinner"
                loc = "need_dinner"
                # mock_meal = True
            name = "Lunch"
            amount = m

        elif loc == "need_snack_2":
            loc = "need_dinner"
            name = "Snack 2"
            amount = m2_stored

        else: # loc == "need_dinner
            loc = "need_breakfast"
            name = "Dinner"
            amount = m
        t += d
        times += [t]
        # meals_print += [(name, "h = " + str(t%24), "g = " + str(amount))]
        meals += [(t, float(amount))]
        '''if mock_meal:
            times += [t + 0.01]
            meals += [("-", "h = " + str(t + 0.01), "0.0")]'''
        if loc == "need_breakfast":
            t = int(t+ (24 - t%24))
    return meals #, meals_print
