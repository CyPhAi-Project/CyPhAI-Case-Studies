import json
import random
import time
from datetime import timedelta
import plotly.graph_objects as go

import numpy as np

from staliro import Trace, optimizers, staliro
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim

from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.params import get_meal_space, get_whole_space
from symbolic_timed_automata.simglucose.simglucose_simobj import PATIENT_NAMES, build_sim_obj
from symbolic_timed_automata.simglucose.utils import get_penalties


def build_simglucose_wrapper(patient, horizon:int):
    def simglucose_wrapper(inputs: Blackbox.Inputs) -> Trace:
        patient_name = patient
        meals = [
            (inputs.static["breakfast_time"], inputs.static["breakfast_size"]),
            (inputs.static["snack1_time"], inputs.static["snack1_size"]),
            (inputs.static["lunch_time"], inputs.static["lunch_size"]),
            (inputs.static["snack2_time"], inputs.static["snack2_size"]),
            (inputs.static["dinner_time"], inputs.static["dinner_size"]),
            (inputs.static["snack3_time"], inputs.static["snack3_size"]),
        ]
        sim_obj = build_sim_obj(meals, patient_name, sim_time_minutes=horizon)
        trace = sim(sim_obj)

        # Shift time stamps and scale to minutes
        timepoints = (trace.index - trace.index[0]) / timedelta(minutes=1)
        return Trace(times=timepoints, states=trace.values)
    return simglucose_wrapper



if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)

    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "../out/falsification/staliro_unconstrained"

    BG = "BG"
    BG_COL = 0
    requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
    spec = rtamt.parse_dense(requirement, {BG: BG_COL})

    costfun = build_simglucose_wrapper(PATIENT_NAMES[args.patient_name], args.horizon)

    params_dict = dict(paitent_name=args.patient_name,
                       horizon=args.horizon,
                       max_opt_iters=args.max_opt_iters,
                       repetitions=args.repetitions,
                       dist_factor=args.dist_factor,
                       seeds=runs_seeds)

    dump_data = dict(runs=[], params=params_dict, falsified=0)
    start_time = time.time()

    meal_space = get_meal_space(args.dist_factor)
    falsified = 0

    for run_idx, run_seed in enumerate(runs_seeds):

        optimizer = optimizers.DualAnnealing(min_cost=1e-6)
        options = TestOptions(
            runs=1,
            iterations=args.max_opt_iters,
            tspan=(0.0, args.horizon),
            static_inputs=get_whole_space(args.dist_factor),
            seed=run_seed)

        run_start_time = time.time()

        blackbox_obj = blackbox(costfun, step_size=1.0)

        runs = staliro(blackbox_obj, spec, optimizer, options)
        run_elapsed_time = time.time() - run_start_time

        run = runs[0]

        run_history = []

        steps = run.evaluations
        # step: Evaluation
        # - sample (staliro.Sample): the input
        # - cost (float): the objective function cost
        # - extra (Series): the trace. Iterable with items, pairs (timestamp, Blood Glucose)
        run = runs[0]
        for i, e in enumerate(run.evaluations):
            run_history.append(dict(iteration=i, cost=e.cost, violated=True if e.cost < 0 else False,
                                    feasible=True if get_penalties(meal_space,e.sample)["total"] <= 0 else False))

        # Generate line plot for blood glucose over time
        figure = go.Figure()
        figure.update_layout(xaxis_title="time (hrs)", yaxis_title="Blood Glucose")
        figure.add_hline(y=70, line_color="red")
        figure.add_hline(y=350, line_color="red")
        res = [f"iteration {i + 1} cost: {e.cost} {'== VIOLATED' if e.cost < 0 else ''}" for i, e in
               enumerate(run.evaluations)]

        violation = [e.sample for e in run.evaluations if e.cost < 0]
        meal_space = get_meal_space(args.dist_factor)

        if len(violation) > 0:
            is_feasible = get_penalties(meal_space, violation[0])["total"] <= 0
            falsified += 1
            dump_data["falsified"] += 1
        else:
            is_feasible = None

        for s in res:
            print(s)

        for i, ev in enumerate(run.evaluations):
            trace = ev.extra.trace
            figure.add_trace(
                go.Scatter(
                    x=[t / 60 for t in list(trace.times)],
                    y=[state[BG_COL] for state in trace.states],
                    mode="lines",
                    name=f"{BG}{i}",
                )
            )

        import os
        run_dump_path = f"{output_path}/{run_idx + 1}"
        if not os.path.exists(run_dump_path):
            os.makedirs(run_dump_path)

        figure.write_image(f"{run_dump_path}/bg.jpeg")
        dump_data["runs"].append(run_history)
        with open(run_dump_path + "/dump.json", "w+") as rf:
            json.dump(
                obj=dict(history=run_history,
                         elapsed_time=run_elapsed_time,
                         falsified=True if len(violation) > 0 else False,
                         seed=run_seed,
                         is_solution_feasible=is_feasible),
                fp=rf, indent=2, sort_keys=True)
    # end runs
    end_time = time.time()

    total_elapsed_time = end_time - start_time
    print(f"Elapsed time: {total_elapsed_time:.4f} seconds")

    dump_data["total_elapsed_time"] = total_elapsed_time

    with open(f"{output_path}/dump.json", "w+") as f:
        json.dump(obj=dump_data, fp=f, indent=2, sort_keys=True)

