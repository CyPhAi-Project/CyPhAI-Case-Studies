from syma.generation.input_generator import InputGenerator

STA_OUT_FNAME = "sta/output/sta_product.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/concrete_trajectories.json"
INITIAL_VALUES = {"m": 0}

def generate_meals(n_scenarios, sta_input_gen: InputGenerator,
                   abstract_traj_fname=None, concrete_traj_fname=None):
    if not abstract_traj_fname:
        abstract_traj_fname = ABSTRACT_TRAJ_FNAME
    if not concrete_traj_fname:
        concrete_traj_fname = CONCRETE_TRAJ_FNAME
    scenarios = sta_input_gen.generate_uniform(abstract_traj_fname,concrete_traj_fname, n_scenarios)
    return scenarios, sta_input_gen


def build_meals(concrete_trajectory: dict) -> list[tuple[float, list[float]]]:
    meals: list[tuple[float, list[float]]] = []
    t = 0

    for meal in concrete_trajectory:
        d = round(meal['delay'], 2)
        m = round(meal['vars']['m'], 1)
        action = meal['action']

        t += d
        meals += [(t, float(m))]
        if "to_breakfast" in action:
            # Go to next midnight, i.e. the next multiple of 24 that is >= t
            t = (t + 23) // 24 * 24 # or t = int(t+ (24 - t%24))
    return meals

labels_to_meals = {"breakfast_to_snack_1": "breakfast",
"breakfast_to_lunch":"breakfast",
"snack_1_to_lunch":"snack1",
"lunch_to_snack_2_no_snack_1":"lunch",
"lunch_to_snack_2_with_s1":"lunch",
"lunch_with_snack_1_to_dinner":"lunch",
"snack_2_to_dinner":"snack2",
"dinner_to_breakfast_no_snack_3":"dinner",
"dinner_to_snack_3":"dinner",
"snack3_to_breakfast":"snack3"}


def build_meals_equivalence_testing(concrete_trajectory: dict) -> dict:
    plan = {}
    t = 0
    for meal in concrete_trajectory:
        d = round(meal['delay'], 2)
        m = meal['vars']['m']   # round(meal['vars']['m'], 1)
        action = meal['action']
        meal = labels_to_meals[action]
        t += d
        if f"{meal}_time" not in plan:
            plan[f"{meal}_time"] = t
            plan[f"{meal}_size"] = m
        if "to_breakfast" in action:
            t = (t + 23) // 24 * 24
            break
    if "snack1_time" not in plan:
        plan["snack1_time"] = 11.0
        plan["snack1_size"] = 0.0
    if "snack2_time" not in plan:
        plan["snack2_time"] = 16.0
        plan["snack2_size"] = 0.0
    if "snack3_time" not in plan:
        plan["snack3_time"] = 21.0
        plan["snack3_size"] = 0.0
    return plan