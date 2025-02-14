import random
import time
from typing import Literal
from pandas import DataFrame
import numpy as np

from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.controller.pid_ctrller import PIDController
from simglucose.simulation.sim_engine import batch_sim

from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.params import get_meal_space, NUM_MEALS
from symbolic_timed_automata.simglucose.penalties import get_penalties
from symbolic_timed_automata.simglucose.simglucose_simobj import build_sim_obj, FoxPIDController, FOXPID_PARAMS
from symbolic_timed_automata.simglucose.sta.build_automaton_six_meals import build_sa_three_snacks
from symbolic_timed_automata.simglucose.generate_meals import build_meals_equivalence_testing, generate_meals
from syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.simglucose.utils import get_random_meal_plan


def batch_simglucose(patient_name,
                     meal_plans: list,
                     horizon) -> list[DataFrame]:


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


def generate_random_meals_rejection_sampling(meal_space, n_meal_plans, dist_factor):
    meal_plans = []
    trials = 0
    while len(meal_plans) < n_meal_plans:
        trials += 1
        mp = get_random_meal_plan(dist_factor)
        if get_penalties(meal_space, mp)["total"] <= 0:
            meal_plans.append([
                (mp["breakfast_time"], mp["breakfast_size"]),
                (mp["snack1_time"], mp["snack1_size"]),
                (mp["lunch_time"], mp["lunch_size"]),
                (mp["snack2_time"], mp["snack2_size"]),
                (mp["dinner_time"], mp["dinner_size"]),
                (mp["snack3_time"], mp["snack3_size"])
            ])
    return meal_plans, trials



if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)
    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "../../../out/sampling/rejection"

    n_meal_plans = args.max_opt_iters
    meal_space = get_meal_space(args.dist_factor)
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
        sta, STA_OUT_FNAME, "../../lib/wordgen",
        length=NUM_MEALS,
        postprocessing_fun=build_meals_equivalence_testing
    )
    bg = "BG"

    dump_data = dict(runs=[], params=params_dict, falsified=0)
    start_time = time.time()
    total_generation_time = 0
    falsified = 0
    rejection_rates = []

    gen_start_time = time.time()
    random_meal_plans, _ = generate_meals(n_meal_plans, sta_input_gen, abstract_traj_fname, concrete_traj_fname)
    run_gen_time = time.time() - gen_start_time
    total_generation_time += run_gen_time

    print(f"Generation took {run_gen_time:.2f} seconds")  # {timedelta(seconds=run_gen_time)}")

    r = 0
    for i, plan in enumerate(random_meal_plans):
        if i % 100 == 0:
            print(f"= Checked up to {i}. Found {r} equivalence violations")
        penalties = get_penalties(meal_space, plan)
        if penalties["total"] > 0:
            print(f"\tPlan {i} is invalid")
            r += 1
            if penalties["lunch_size"] > 0:
                print("Lunch size violated:", plan["lunch_size"] )
            else:
                print(penalties)
                print(plan)


