import random
import os
import json
import time

import numpy as np
from apricopt.solving.blackbox.NOMAD.NOMADSolver import NOMADSolver

from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.generate_meals import build_meals
from symbolic_timed_automata.simglucose.params import NUM_MEALS
from symbolic_timed_automata.simglucose.simglucose_simobj import PATIENT_NAMES
from syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.simglucose.falsification.blackbox.simglucose_sta_blackbox import SimGlucoseSTABlackBox
from symbolic_timed_automata.simglucose.sta.build_simglucose_sta import build_simglucose_sta

WORDGEN_PATH = "/home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/lib/wordgen"



if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)
    # Generate a random seed for each run
    runs_seeds = [int(x) for x in np.random.randint(1, 65536, args.repetitions)]

    if args.output is not None:
        output_path = args.output
    else:
        output_path = "../../experiments/output/simglucose/falsification/nomad_sta"

    sta = build_simglucose_sta(dist_factor=args.dist_factor)
    STA_OUT_FNAME = f"{output_path}/sta_product.prism"
    ABSTRACT_TRAJ_FNAME = f"{output_path}/abstract_trajectories.json"
    CONCRETE_TRAJ_FNAME = f"{output_path}/concrete_trajectories.json"

    sta_input_gen: InputGenerator = InputGenerator(
        sta, STA_OUT_FNAME, WORDGEN_PATH,
        length=NUM_MEALS,
        postprocessing_fun=build_meals
    )

    patient_name = PATIENT_NAMES[args.patient_name]

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
        print(f"Starting NOMAD run #{run_idx + 1}")
        np.random.seed(run_seed)
        random.seed(run_seed)



        sg_black_box = SimGlucoseSTABlackBox(
            input_generator=sta_input_gen,
            patient_name=patient_name,
            horizon=args.horizon,
            num_meals=NUM_MEALS)

        solver = NOMADSolver()
        solver_params = {"solver_params":
                         ["STOP_IF_FEASIBLE true",
                          f"MAX_BB_EVAL {args.max_opt_iters}",
                          f"SEED {run_seed}"]}

        run_start_time = time.time()
        result = solver.solve(sg_black_box, solver_params, print_bb_evals=True)
        run_elapsed_time = time.time() - run_start_time

        run_history = sg_black_box.history
        res = [f"iteration {step['iteration'] + 1} cost: {step['cost']} {'== VIOLATED' if step['cost'] < 0 else ''}" for step in
               run_history]
        for s in res:
            print(s)

        violation = [step for step in run_history if step['cost'] < 0]
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
