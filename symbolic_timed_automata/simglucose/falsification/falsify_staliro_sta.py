import random
import time
import os
import json
from datetime import timedelta
from typing import Callable

import plotly.graph_objects as go

import numpy as np

from staliro import Trace, optimizers, staliro
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim

from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.params import NUM_MEALS
from symbolic_timed_automata.simglucose.simglucose_simobj import PATIENT_NAMES, build_sim_obj
from symbolic_timed_automata.simglucose.sta.build_automaton_six_meals import build_sa_three_snacks
from symbolic_timed_automata.simglucose.generate_meals import build_meals
from syma.generation.input_generator import InputGenerator

def build_simglucose_wrapper(input_generator: InputGenerator, patient_name, horizon: int) -> Callable[[Blackbox.Inputs], Trace]:
    def simglucose_wrapper(inputs: Blackbox.Inputs) -> Trace:
        # we assume the input is a dictionary like
        # { "delay_1": <value>, "transition_1": <value>, "var1_1": value, ..., "varK_1": value,
        #   "delay_2": <value>, "transition_2": <value>, "var1_2": value, ..., "varK_2": value,
        # ... }
        # So, for each transition, we have
        # 1) the value in [0,1] used to choose the delay
        # 2) the value in [0,1] used to choose the transition
        # 3) for each symbolic variable, the value in [0,1] used to generate its value

        meals = input_generator.generate_from_point_in_hypercube(inputs.static)
        # print(meals)
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
    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "../out/falsification/staliro_sta"
    BG = "BG"
    BG_COL = 0
    requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
    spec = rtamt.parse_dense(requirement, {BG: BG_COL})

    patient_name = PATIENT_NAMES[args.patient_name]


    sta = build_sa_three_snacks(dist_factor=args.dist_factor)
    STA_OUT_FNAME = f"{output_path}/sta_product.prism"
    ABSTRACT_TRAJ_FNAME = f"{output_path}/abstract_trajectories.json"
    CONCRETE_TRAJ_FNAME = f"{output_path}/concrete_trajectories.json"

    sta_input_gen: InputGenerator = InputGenerator(
                sta, STA_OUT_FNAME, "../../lib/wordgen",
                length=NUM_MEALS,
                postprocessing_fun=build_meals
        )
    n_var = len(sta_input_gen.sta.var_names)

    # Build search space
    search_space: dict[str, tuple[float, float]] = dict()
    for i in range(1, NUM_MEALS + 1):
        # start_idx = (i-1)*(2+n_var)
        search_space[f"delay_{i}"] = (0, 1)
        search_space[f"transition_{i}"] = (0, 1)
        for j in range(1, n_var + 1):
            search_space[f"{sta_input_gen.sta.var_names[j - 1]}_{i}"] = (0, 1)

    blackbox_function = build_simglucose_wrapper(sta_input_gen,  patient_name, args.horizon)

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
            static_inputs=search_space,
            seed=run_seed)

        run_start_time = time.time()

        # Run
        blackbox_obj = blackbox(blackbox_function, step_size=1.0)
        runs = staliro(blackbox_obj, spec, optimizer, options)
        run_elapsed_time = time.time() - run_start_time

        run = runs[0]

        run_history = []
        steps = run.evaluations
        for i, e in enumerate(run.evaluations):
            run_history.append(
                dict(iteration=i, cost=e.cost,
                     violated=True if e.cost < 0 else False))


        figure = go.Figure()
        figure.update_layout(xaxis_title="time (hrs)", yaxis_title="Blood Glucose")
        figure.add_hline(y=70, line_color="red")
        figure.add_hline(y=350, line_color="red")
        res = [f"iteration {i+1} cost: {e.cost} {'== VIOLATED' if e.cost < 0 else ''}" for i, e in enumerate(run.evaluations)]
        for s in res:
            print(s)
        violation = [e.sample for e in run.evaluations if e.cost < 0]
        if len(violation) > 0:
            falsified += 1
            dump_data["falsified"] += 1

        for i, ev in enumerate(run.evaluations):
            trace = ev.extra.trace
            figure.add_trace(
                go.Scatter(
                    x=[t/60 for t in list(trace.times)],
                    y=[state[BG_COL] for state in trace.states],
                    mode="lines",
                    # line_color="green",
                    name=f"{BG}{i}",
                )
            )

        run_dump_path = f"{output_path}/{run_idx+1}"
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
