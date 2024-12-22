import json
import os
import random
import sys
import time
from datetime import timedelta
from typing import Literal
from pandas import DataFrame

from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.controller.pid_ctrller import PIDController
from simglucose.simulation.sim_engine import batch_sim
import stlrom
import numpy as np

from cli import get_command_line_arguments
from params import NUM_MEALS
from simglucose_simobj import PATIENT_NAMES, build_sim_obj, FoxPIDController, FOXPID_PARAMS
from sta.automaton_three_snacks import build_sa_three_snacks
from sta.build_automaton_simplified import build_sa
from sta.generate_meals import generate_meals, build_meals_simplified
from sta.input_generator import InputGenerator
from utils import evaluate_robustness


def batch_simglucose(patient_name,
                     meal_plans: list,
                     horizon) -> list[DataFrame]:

    #sta_input_gen.to_file(meal_plans, f"{output_path}/meal_plans.json")

    sim_obj_list = []
    try:
        # Build controller
        sel_ctrl = "BB"  # type: Literal["BB", "PID", "FoxPID"]
        if sel_ctrl == "BB":
            ctrl = BBController(target=140)  # Specify target BG
        elif sel_ctrl == "PID":
            ctrl = PIDController(P=0.001, I=0.00001, D=0.001, target=140)
        elif sel_ctrl == "FoxPID":
            kp, ki, kd = FOXPID_PARAMS[patient_name]
            ctrl = FoxPIDController(setpoint=112.517, kp=kp, ki=ki, kd=kd, basal=None)

        for meal_plan in meal_plans:
            # Create scenarios
            sim_obj_list.append(build_sim_obj(
                meals=meal_plan,
                patient_name=patient_name,
                controller=ctrl, sim_time_minutes=horizon))
    except KeyError:
        print(f"cannot find PID params for patient {patient_name}")

    # Batch simulation
    return batch_sim(sim_obj_list, parallel=True)


if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)
    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "out/sampling/sta"

    n_meal_plans = args.max_opt_iters
    params_dict = dict(patient_name=args.patient_name,
                       horizon=args.horizon,
                       max_opt_iters=args.max_opt_iters,
                       repetitions=args.repetitions,
                       dist_factor=args.dist_factor,
                       seeds=runs_seeds)

    # Build STA and signal generator
    sta = build_sa_three_snacks(dist_factor=args.dist_factor)
    STA_OUT_FNAME = f"{output_path}/sta_product.prism"
    abstract_traj_fname = f"{output_path}/abstract_trajectories.json"
    concrete_traj_fname = f"{output_path}/concrete_trajectories.json"

    sta_input_gen: InputGenerator = InputGenerator(
        sta, STA_OUT_FNAME, "sta/lib/wordgen",
        length=NUM_MEALS,
        postprocessing_fun=build_meals_simplified
    )

    bg = "BG"

    dump_data = dict(runs=[], params=params_dict, falsified=0)
    start_time = time.time()
    total_generation_time = 0
    falsified = 0

    for run_idx, run_seed in enumerate(runs_seeds):
        print(f"\n================\nRun {run_idx + 1}/{len(runs_seeds)}")
        np.random.seed(run_seed)
        random.seed(run_seed)
        run_start_time = time.time()
        # Generate meal plans uniformly at random
        gen_start_time = time.time()
        random_meal_plans, _ = generate_meals(n_meal_plans, sta_input_gen, abstract_traj_fname, concrete_traj_fname)
        run_gen_time = time.time() - gen_start_time
        total_generation_time += run_gen_time

        print(f"Generation took {run_gen_time:.2f} seconds") # {timedelta(seconds=run_gen_time)}")

        sim_start_time = time.time()
        # Simulate all meal plans in parallel
        sim_results = batch_simglucose(patient_name=PATIENT_NAMES[args.patient_name],
                                   meal_plans=random_meal_plans,
                                   horizon=args.horizon)
        run_sim_time = time.time() - sim_start_time
        res_robustness = [evaluate_robustness(sim_result, bg, args.horizon) for sim_result in sim_results]
        run_elapsed_time = time.time() - run_start_time
        run_dump_path = f"{output_path}/{run_idx + 1}"
        if not os.path.exists(run_dump_path):
            os.makedirs(run_dump_path)

        run_falsified = True if any([r<0 for r in res_robustness]) else False
        if run_falsified:
            dump_data["falsified"] += 1
            print(f"\tRun {run_idx + 1} FALSIFIED")

        run_dump_data = dict(evaluations=res_robustness,
                             seed=run_seed,
                             run_total_time=run_elapsed_time,
                             run_generation_time=run_gen_time,
                             run_simulation_time=run_sim_time,
                             falsified=run_falsified)

        # Dump each run to file separately
        dump_data["runs"].append(run_dump_data)
        with open(run_dump_path + "/dump.json", "w+") as rf:
            json.dump(
                obj=run_dump_data,
                fp=rf, indent=2, sort_keys=True)

    dump_data["total_time"] = time.time() - start_time
    # Dump all runs together
    with open(f"{output_path}/dump.json", "w+") as f:
        json.dump(obj=dump_data, fp=f, indent=2, sort_keys=True)

