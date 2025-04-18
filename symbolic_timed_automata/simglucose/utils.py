import random
import sys
from datetime import timedelta

import numpy as np
import rtamt

# import stlrom

from symbolic_timed_automata.simglucose.params import get_meal_space, get_whole_space
from symbolic_timed_automata.simglucose.penalties import get_penalties


def get_random_meal_plan(dist_factor: float):
    S = get_whole_space(dist_factor)
    mp = {}
    for param, p_range in S.items():
        mp[param] = p_range[0] + (p_range[1] - p_range[0]) * np.random.random()
    return mp

def get_feasible_random_meal_plan(dist_factor: float):
    meal_space = get_meal_space(dist_factor)
    mp = get_random_meal_plan(dist_factor)
    failures = 0
    while True:

        if get_penalties(meal_space,mp)["total"] == 0:

            print(f"Feasible mp: {mp}")
            return mp
        '''failures += 1
        print(f"Failures: {failures}")
        print(f"Penalties: {get_penalties(meal_space,mp)['breakfast_time']}")
        print(f"Breakfast time: {mp['breakfast_time']}")'''

        mp = get_random_meal_plan(dist_factor)


def evaluate_robustness(sim_result, bg, horizon, for_penalties=False) -> float | tuple[float, dict]:
    bg_trace: list[list[float]] = []
    times = []
    item_iter = sim_result[bg].items()
    # Get the initial time stamp and value
    t0, v0 = next(item_iter)  # type: ignore
    bg_trace.append([0.0, v0])

    for t_datetime, value in item_iter:
        t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
        bg_trace.append([t, value])
        times.append(t)

    spec = rtamt.StlDenseTimeSpecification()
    spec.name = 'STL Dense-time Offline Monitor'
    spec.declare_var(bg, 'float')
    spec.set_var_io_type(bg, 'input')
    spec.spec = f"always[0, {horizon}](({bg} > 70) and ({bg} < 350))"
    try:
        spec.parse()
    except rtamt.RTAMTException as err:
        print('RTAMT Exception: {}'.format(err))
        sys.exit()

    robustness = spec.evaluate([bg, bg_trace])[-1][1]

    # print('Robustness: {}'.format(rob))
    if not(for_penalties):
        return robustness
    else:
        return robustness, dict(times=times, states=bg_trace, robustness=robustness)

'''def evaluate_robustness(sim_result, bg, horizon) -> float:
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
    return robustness_interval[1]'''

def gen_time_with_constraint(hl, hu, previous_time, dl, du):
    meal_time = random.uniform(hl, hu)
    while True:
        if dl <= meal_time - previous_time <= du:
            return meal_time
        else:
            meal_time = random.uniform(hl, hu)

def simglucose_isotropic_sampling(n_signals: int, dist_factor, for_falsification=False):
    inputs = get_meal_space(dist_factor)
    signals = []
    for i_signal in range(n_signals):
        signal: list[dict[str, float | str | dict[str, float]]] | list[tuple[float, float]] = []
        current_time: float = 0.0

        # Take breakfast
        do_take_snack_1 = random.uniform(0, 1) < 0.5

        if do_take_snack_1:
            # [breakfast_to_snack_1] (state=3) & (h>=5)&(h<=8) -> (0.5) : (state'=5) & (d'=0)&(t'=0);
            breakfast_size = random.uniform(inputs['breakfast_size_with_snack_1'][0],
                                            inputs['breakfast_size_with_snack_1'][1])
            breakfast_time = random.uniform(inputs['breakfast_time_with_snack_1'][0],
                                            inputs['breakfast_time_with_snack_1'][1])
            action = "breakfast_to_snack_1"
        else:
            # [breakfast_to_lunch] (state=3) & (h>=6)&(h<=9) -> (0.5) : (state'=1) & (d'=0)&(t'=0);
            breakfast_size = random.uniform(inputs['breakfast_size_no_snack_1'][0],
                                            inputs['breakfast_size_no_snack_1'][1])
            breakfast_time = random.uniform(inputs['breakfast_time_no_snack_1'][0],
                                            inputs['breakfast_time_no_snack_1'][1])
            action = "breakfast_to_lunch"
        if not for_falsification:
            signal.append(dict(vars=dict(m=breakfast_size), action=action, delay=breakfast_time, date=breakfast_time))
        else:
            signal.append((breakfast_time, breakfast_size))

        current_time = current_time + breakfast_time
        # Take snack 1
        if do_take_snack_1:
            # [snack_1_to_lunch: ((m) >= (9.5)) and ((m) <= (10.5))] (state=5) & (h>=9)&(h<=11) -> (1.0) : (state'=0) & (t'=0);
            snack1_size = random.uniform(inputs['snack_1_size'][0], inputs['snack_1_size'][0])
            snack1_time = random.uniform(inputs['snack_1_time'][0], inputs['snack_1_time'][1])
            action = "snack1_to_lunch"

            if not for_falsification:
                signal.append(
                    dict(vars=dict(m=snack1_size), action=action, delay=snack1_time - current_time, date=snack1_time))
            else:
                signal.append((snack1_time, snack1_size))


            current_time = snack1_time

        do_take_snack_2 = random.uniform(0, 1) < 0.5
        # Take lunch
        if do_take_snack_1:
            if do_take_snack_2:
                # [lunch_to_snack_2_with_s1: ((m) >= (64.0)) and ((m) <= (66.0))] (state=0) & (h>=12)&(h<=15)&(d>=4)&(d<=7) -> (0.5) : (state'=2) & (d'=0)&(t'=0);
                lunch_time = gen_time_with_constraint(
                    inputs['lunch_time_with_snack_1_and_2'][0],
                    inputs['lunch_time_with_snack_1_and_2'][1],
                    breakfast_time,
                    inputs['lunch_d_with_snack_1_and_2'][0],
                    inputs['lunch_d_with_snack_1_and_2'][1],
                )

                lunch_size = random.uniform(
                    inputs['lunch_size_with_snack_1_and_2'][0],
                    inputs['lunch_size_with_snack_1_and_2'][1])
            else:
                lunch_time = gen_time_with_constraint(
                    inputs['lunch_time_no_snack_2'][0],
                    inputs['lunch_time_no_snack_2'][1],
                    breakfast_time,
                    inputs['lunch_d_no_snack_2'][0],
                    inputs['lunch_d_no_snack_2'][1])

                # 	[lunch_with_snack_1_to_dinner: ((m) >= (79.0)) and ((m) <= (81.0))] (state=0) & (h>=12)&(h<=15)&(d>=4)&(d<=7) -> (0.5) : (state'=6) & (d'=0)&(t'=0);
                lunch_size = random.uniform(
                    inputs['lunch_size_no_snack_2'][0],
                    inputs['lunch_size_no_snack_2'][1],
                )
                action = "lunch_with_snack_1_to_dinner"
        else:
            # [lunch_to_snack_2_no_snack_1: ((m) >= (69.0)) and ((m) <= (71.0))] (state=1) & (h>=12)&(h<=15)&(d>=3)&(d<=6) -> (1.0) : (state'=2) & (d'=0)&(t'=0);

            lunch_time = gen_time_with_constraint(
                inputs['lunch_time_no_snack_1'][0],
                inputs['lunch_time_no_snack_1'][1],
                breakfast_time,
                inputs['lunch_d_no_snack_1'][0],
                inputs['lunch_d_no_snack_1'][1])

            lunch_size = random.uniform(
                inputs['lunch_size_no_snack_1'][0],
                inputs['lunch_size_no_snack_1'][1])
            action = "lunch_to_snack_2_no_snack_1"

        if not for_falsification:
            signal.append(
                dict(vars=dict(m=lunch_size), action=action, delay=lunch_time - current_time, date=lunch_time))
        else:
            signal.append((lunch_time, lunch_size))

        current_time = lunch_time

        # Take snack 2
        # 	[snack_2_to_dinner: ((m) >= (9.5)) and ((m) <= (10.5))] (state=2) & (h>=14)&(h<=16) -> (1.0) : (state'=6) & (t'=0);
        if do_take_snack_2:
            snack2_size = random.uniform(
                inputs['snack_2_size'][0],
                inputs['snack_2_size'][1],
            )
            snack2_time = random.uniform(
                inputs['snack_2_time'][0],
                inputs['snack_2_time'][1]
            )
            action = "snack2_to_dinner"

            if not for_falsification:
                signal.append(
                    dict(vars=dict(m=snack2_size), action=action, delay=snack2_time - current_time, date=snack2_time))
            else:
                signal.append((snack2_time, snack2_size))
            current_time = snack2_time

        # Take dinner
        do_take_snack_3 = random.uniform(0, 1) < 0.5

        if do_take_snack_3:
            # [dinner_to_snack_3: ((m) >= (69.0)) and ((m) <= (71.0))] (state=6) & (h>=16)&(h<=20)&(d>=4)&(d<=6) -> (0.5) : (state'=4) & (t'=0);

            dinner_time = gen_time_with_constraint(
                inputs['dinner_time_with_snack_3'][0],
                inputs['dinner_time_with_snack_3'][1],
                lunch_time,
                inputs['dinner_d_with_snack_3'][0],
                inputs['dinner_d_with_snack_3'][1]
            )

            dinner_size = random.uniform(
                inputs['dinner_size_with_snack_3'][0],
                inputs['dinner_size_with_snack_3'][1]
            )
            action = "dinner_to_snack_3"
        else:
            # [dinner_to_breakfast_no_snack_3: ((m) >= (84.0)) and ((m) <= (86.0))] (state=6) & (h>=17)&(h<=21)&(d>=5)&(d<=7) -> (0.5) : (state'=3) & (d'=0)&(h'=0)&(t'=0);
            dinner_time = gen_time_with_constraint(
                inputs['dinner_time_no_snack_3'][0],
                inputs['dinner_time_no_snack_3'][1],
                lunch_time,
                inputs['dinner_d_no_snack_3'][0],
                inputs['dinner_d_no_snack_3'][1]
            )

            dinner_size = random.uniform(
                inputs['dinner_size_no_snack_3'][0],
                inputs['dinner_size_no_snack_3'][1]
            )
            action = "dinner_to_breakfast_no_snack_3"
        if not for_falsification:
            signal.append(
                dict(vars=dict(m=dinner_size), action=action, delay=dinner_time - current_time, date=dinner_time))
        else:
            signal.append((dinner_time, dinner_size))

        # Take snack 3
        if do_take_snack_3:
            # [snack3_to_breakfast: ((m) >= (9.5)) and ((m) <= (10.5))] (state=4) & (h>=20)&(h<=23) -> (1.0) : (state'=3) & (d'=0)&(h'=0)&(t'=0);
            snack3_size = random.uniform(
                inputs['snack_3_size'][0],
                inputs['snack_3_size'][1],
            )
            snack3_time = random.uniform(
                inputs['snack_3_time'][0],
                inputs['snack_3_time'][1]
            )
            action = "snack3_to_breakfast"

            if not for_falsification:
                signal.append(
                    dict(vars=dict(m=snack3_size), action=action, delay=snack3_time - dinner_time, date=snack3_time))
            else:
                signal.append((snack3_time, snack3_size))

        signals.append(signal)
    return signals


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
        
        
