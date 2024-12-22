import json
import random
import time
from datetime import timedelta
from typing import Callable

import plotly.graph_objects as go

import numpy as np

import staliro
import stlrom
from staliro import Trace, optimizers, CostFunc
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim

from cli import get_command_line_arguments
from params import get_meal_space, get_whole_space
from simglucose_simobj import PATIENT_NAMES, build_sim_obj
from utils import get_penalties


def build_cost_function(patient_name, horizon, meal_space):
    @staliro.costfunc()
    def robustness_with_constraint_penalties(inputs: staliro.Sample) -> staliro.Result[float, str]:
        meals = [
            (inputs.static["breakfast_time"], inputs.static["breakfast_size"]),
            (inputs.static["snack1_time"], inputs.static["snack1_size"]),
            (inputs.static["lunch_time"], inputs.static["lunch_size"]),
            (inputs.static["snack2_time"], inputs.static["snack2_size"]),
            (inputs.static["dinner_time"], inputs.static["dinner_size"]),
            (inputs.static["snack3_time"], inputs.static["snack3_size"]),
        ]
        penalties = get_penalties(meal_space, inputs)

        sim_obj = build_sim_obj(meals, patient_name, sim_time_minutes=horizon)
        sim_result = sim(sim_obj)

        robustness, trace = _evaluate_robustness(sim_result, "BG", horizon)
        res_value = robustness + penalties["total"]
        # extra = "feasible" if res_value == robustness else "not feasible"
        print("Robustness: ", robustness)
        print("Cost: ", res_value)

        return staliro.Result(value=res_value, extra=trace)

    return robustness_with_constraint_penalties


def _evaluate_robustness(sim_result, bg, horizon):
    stl_monitor = stlrom.STLDriver()
    # Spec from "Towards a verified artificial pancreas: Challenges and solutions for runtime verification.", RV 2015
    spec = f"""
                        signal {bg}

                        safety := alw_[0, {horizon}] (({bg}[t] > 70) and ({bg}[t] < 350))
                        """
    times = []
    bg_trace = []
    # parse the formulas
    succ = stl_monitor.parse_string(spec)
    if not succ:
        print("Error when parsing STL spec formula")
        return float("Inf")

    item_iter = sim_result[bg].items()
    # Get the initial time stamp and value
    t0, v0 = next(item_iter)  # type: ignore
    stl_monitor.add_sample([0.0, v0])

    for t_datetime, value in item_iter:
        t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
        stl_monitor.add_sample([t, value])
        times.append(t)
        bg_trace.append(value)

    robustness = stl_monitor.get_online_rob("safety", 0.0)[1]
    return robustness, dict(times=times, states=bg_trace, robustness=robustness)


if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)

    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "out/falsification/staliro_penalties"

    BG = "BG"
    BG_COL = 0
    requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
    spec = rtamt.parse_dense(requirement, {BG: BG_COL})

    patient_name = PATIENT_NAMES[args.patient_name]
    meal_space = get_meal_space(args.dist_factor)
    costfun = build_cost_function(patient_name, args.horizon, meal_space)

    params_dict = dict(paitent_name=args.patient_name,
                       horizon=args.horizon,
                       max_opt_iters=args.max_opt_iters,
                       repetitions=args.repetitions,
                       dist_factor=args.dist_factor,
                       seeds=runs_seeds)

    dump_data = dict(runs=[], params=params_dict, falsified=0)
    start_time = time.time()

    falsified = 0

    for run_idx, run_seed in enumerate(runs_seeds):
        optimizer = optimizers.DualAnnealing(min_cost=1e-6)
        options = TestOptions(
            runs=1,
            iterations=args.max_opt_iters,
            tspan=(0.0, args.horizon),
            # static_inputs=get_meal_space(args.dist_factor),
            static_inputs=get_whole_space(args.dist_factor),
            seed=run_seed)

        run_start_time = time.time()
        # Run falsification
        runs = staliro.staliro(costfun, optimizer, options)

        run_elapsed_time = time.time() - run_start_time

        run = runs[0]

        run_history = []

        steps = run.evaluations
        # step: Evaluation
        # - sample (staliro.Sample): the input
        # - cost (float): the objective function cost
        # - extra (Series): the trace. Iterable with items, pairs (timestamp, Blood Glucose)
        for i, e in enumerate(run.evaluations):
            run_history.append(
                dict(iteration=i, cost=e.cost, violated=e.cost < 0,
                     robustness=e.extra["robustness"]))

        figure = go.Figure()
        figure.update_layout(xaxis_title="time (hrs)", yaxis_title="Blood Glucose")
        figure.add_hline(y=70, line_color="red")
        figure.add_hline(y=350, line_color="red")
        res = [f"iteration {i+1} cost: {e.cost} {'== VIOLATED' if e.cost < 0 else ''}" for i, e in enumerate(run.evaluations)]

        violation = [e.sample for e in run.evaluations if e.cost < 0]
        if len(violation) > 0:
            falsified += 1
            dump_data["falsified"] += 1
        for s in res:
            print(s)


        for i, ev in enumerate(run.evaluations):
            trace = ev.extra
            figure.add_trace(
                go.Scatter(
                    x=trace["times"],
                    y=trace["states"],
                    mode="lines",
                    # line_color="green",
                    name=f"{BG}{i}",
                )
            )

        import os

        # checking if the directory demo_folder
        # exist or not.
        run_dump_path  = f"{output_path}/{run_idx+1}"
        if not os.path.exists(run_dump_path):
            os.makedirs(run_dump_path)

        figure.write_image(f"{run_dump_path}/bg.jpeg")
        dump_data["runs"].append(run_history)
        with open(run_dump_path + "/dump.json", "w+") as rf:
            json.dump(
                obj=dict(history=run_history,
                         elapsed_time=run_elapsed_time,
                         falsified=True if len(violation) > 0 else False,
                         seed=run_seed),
                fp=rf, indent=2, sort_keys=True)

    with open(f"{output_path}/dump.json", "w+") as f:
        json.dump(obj=dump_data, fp=f, indent=2, sort_keys=True)