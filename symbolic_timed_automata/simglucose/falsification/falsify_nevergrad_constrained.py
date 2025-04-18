import random
import os
import json
import time

import numpy as np

import nevergrad as ng

from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.falsification.blackbox.simglucose_blackbox_nevergrad import SimGlucoseBlackBoxNG
from symbolic_timed_automata.simglucose.params import get_meal_space
from symbolic_timed_automata.simglucose.penalties import get_penalties
from symbolic_timed_automata.simglucose.simglucose_simobj import PATIENT_NAMES
from symbolic_timed_automata.simglucose.falsification.blackbox.simglucose_blackbox import SimGlucoseBlackBox


if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)
    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "../../experiments/output/simglucose/falsification/nevergrad_constrained"

    patient_name = PATIENT_NAMES[args.patient_name]

    params_dict = dict(paitent_name=args.patient_name,
                       horizon=args.horizon,
                       max_opt_iters=args.max_opt_iters,
                       repetitions=args.repetitions,
                       dist_factor=args.dist_factor,
                       seeds=runs_seeds,
                       initial_feasible=args.initial_feasible)

    dump_data = dict(runs=[], params=params_dict, falsified=0)
    start_time = time.time()

    falsified = 0

    for run_idx, run_seed in enumerate(runs_seeds):
        print(f"Starting Nevergrad run #{run_idx + 1}")
        np.random.seed(run_seed)
        random.seed(run_seed)


        sg_black_box = SimGlucoseBlackBoxNG(
            patient_name, args.horizon, args.dist_factor, initial_feasible=args.initial_feasible)
        initial_values = [sg_black_box.get_optimization_parameter_initial_value(p_id)
                          for p_id in sg_black_box.get_optimization_parameters_ids()]
        lower_bounds = [sg_black_box.get_optimization_parameter_lower_bound(p_id)
                        for p_id in sg_black_box.get_optimization_parameters_ids()]
        upper_bounds = [sg_black_box.get_optimization_parameter_upper_bound(p_id)
                        for p_id in sg_black_box.get_optimization_parameters_ids()]

        param_space = ng.p.Array(init=np.array(initial_values),
                                 #shape=(len(initial_values),),
                                 lower=np.array(lower_bounds),
                                 upper=np.array(upper_bounds))

        param_space.random_state.seed(run_seed)
        # NgIohTuned optimizer: meta optimizer that adapts to the budget and dimensionality of the problem

        objective = sg_black_box.evaluate_objective_np_array
        optimizer = ng.optimizers.NgIohTuned(parametrization=param_space, budget=args.max_opt_iters)

        run_start_time = time.time()
        for _ in range(optimizer.budget):
            meal_plan = optimizer.ask()
            obj_value = objective(meal_plan.value)
            constraint_violation = sg_black_box.get_penalties(meal_plan)
            optimizer.tell(meal_plan, obj_value, constraint_violation=constraint_violation)

            # Check if best value is <= 0 (or another threshold)
            if obj_value <= 0 and sum(constraint_violation) <= 0:
                print("Reached target objective - the meal plan falsifies the safety property!")
                break



        # result = solver.minimize(sg_black_box.evaluate_objective_np_array)
        run_elapsed_time = time.time() - run_start_time

        run_history = sg_black_box.history
        res = [(f"iteration {step['iteration'] + 1} cost: {step['cost']}"
                f" {'== VIOLATED' if step['cost'] < 0 and step['feasible'] else ''}")
               for step in run_history]
        for s in res:
            print(s)

        violation = [step for step in run_history if step['cost'] < 0 and step['feasible']]
        if len(violation) > 0:
            falsified += 1
            dump_data["falsified"] += 1

        run_dump_path = f"{output_path}/{run_idx + 1}"
        if not os.path.exists(run_dump_path):
            os.makedirs(run_dump_path)

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