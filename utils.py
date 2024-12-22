from datetime import timedelta

import numpy as np
import staliro
import stlrom

from params import get_meal_space, get_whole_space



def get_random_meal_plan(dist_factor: float):
    S = get_whole_space(dist_factor)
    mp = {}
    for param, p_range in S.items():
        mp[param] = p_range[0] + (p_range[1] - p_range[0]) * np.random.random()
    return mp


def evaluate_robustness(sim_result, bg, horizon) -> float:
    # Robust monitoring
    stl_monitor = stlrom.STLDriver()
    # Spec from "Towards a verified artificial pancreas: Challenges and solutions for runtime verification.", RV 2015
    spec = f"""
                signal {bg}

                safety := alw_[0, {horizon}] (({bg}[t] > 70) and ({bg}[t] < 350))
                """
    # parse the formulas
    succ = stl_monitor.parse_string(spec)
    if not succ:
        print("Error when parsing STL spec formula")
        raise ValueError

    item_iter = sim_result[bg].items()
    # Get the initial time stamp and value
    t0, v0 = next(item_iter)  # type: ignore
    stl_monitor.add_sample([0.0, v0])

    for t_datetime, value in item_iter:
        t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
        stl_monitor.add_sample([t, value])
    robustness_interval = stl_monitor.get_online_rob("safety", 0.0)
    # print("Robustness Interval:", robustness_interval)
    return robustness_interval[1]



if __name__ ==  "__main__":

    meal_space = get_meal_space(1.0)

    S = get_whole_space(1.0)
    feasible = 0
    for i in range(100):
        # print(i)
        mp = get_random_meal_plan(1.0)
        # print(mp)
        penalties = get_penalties(meal_space, mp)
        if penalties["total"] <= 0:
            feasible += 1
            print(i)
        
        
