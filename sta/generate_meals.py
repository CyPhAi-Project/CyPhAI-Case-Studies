from typing import List, Dict, Tuple

from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from sta.build_automaton_simplified import build_sa
from sta.input_generator import InputGenerator


STA_OUT_FNAME = "sta/output/sta_product.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/concrete_trajectories.json"
INITIAL_VALUES = {"m": 0}


def initialize(n_meals:int = 5, generator:InputGenerator=None):
    sta: SymbolicTimedAutomaton = build_sa()

    if not generator:
        sta_input_gen: InputGenerator = InputGenerator(
            sta, STA_OUT_FNAME, "lib/wordgen",
            length=n_meals,
            postprocessing_fun=build_meals_simplified
        )
    else:
        sta_input_gen = generator
    return sta, sta_input_gen


def generate_meals(n_meals:int = 5, n_scenarios: int = 1, generator:InputGenerator=None):
    sta, sta_input_gen = initialize(n_meals, generator)

    scenarios = sta_input_gen.generate_uniform(ABSTRACT_TRAJ_FNAME,CONCRETE_TRAJ_FNAME, n_scenarios)
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


def build_meals_simplified(concrete_trajectory: dict) -> List[Tuple[float, List[float]]]:
    meals: List[Tuple[float, List[float]]] = []
    t = 0

    for meal in concrete_trajectory:
        d = round(meal['delay'], 2)
        m = round(meal['vars']['m'], 1)
        action = meal['action']

        t += d
        meals += [(t, float(m))]
        if action == "to_breakfast":
            t = int(t+ (24 - t%24))
    return meals
