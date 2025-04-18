import json
import numpy as np

from symbolic_timed_automata.simglucose.penalties import BASE_PENALTY

experiments = ["staliro_unconstrained",
               "staliro_penalties",
               "staliro_sta",
               "nomad_constrained",
               "nomad_sta",
               "nevergrad_sta",
               "nevergrad_constrained",
               "isotropic",
               "uniform_sta"
               ]

# base_path = "../out/three_snacks/falsification/p10/d3.0_i500_r10"
base_path = "/home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification"

results = {}
result_dump_path = "/home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/postprocessed_results"

# limits = [100,200,250,300,350,400,500]
limits = [500]
for l in limits:
    lim_results = {}
    for exp in experiments:
        dump_fname = f"{base_path}/{exp}/dump.json"
        with open(dump_fname, "r") as f:
            expres = json.load(f)
        falsified = 0
        unconstr_feasible = 0
        worst = float("Inf")
        iters = []
        infeasible_iters = []
        tot_generation_time = 0.0
        tot_simulation_time = 0.0
        for run in expres["runs"]:
            infeasible_steps = 0
            violated = False
            if exp not in ["isotropic", "uniform_sta"]:
                for step in run:
                    if step["cost"] > BASE_PENALTY or ("feasible" in step and not step["feasible"]):
                        infeasible_steps += 1
                    '''if step["iteration"] >= l:
                        break'''
                    if step["cost"] < worst:
                        if "feasible" not in step or ("feasible" in step and step["feasible"]):
                            worst = step["cost"]

                    if exp in ["staliro_unconstrained", "staliro_penalties", "staliro_sta", "nomad_sta", "nevergrad_sta"]:
                        if step["violated"]:
                            violated = True
                            falsified += 1
                            if "feasible" not in step or ("feasible" in step and step["feasible"]):
                                unconstr_feasible += 1
                            iters.append(step["iteration"]+1)
                            break
                    else:
                        if step["feasible"] and step["violated"]:
                            violated = True
                            falsified += 1
                            iters.append(step["iteration"]+1)
                            break
                if not violated:
                    iters.append(step["iteration"]+1)
                infeasible_iters.append(infeasible_steps)
            else: # isotropic or uniform_sta
                evaluations = run["evaluations"]
                for i, cost in enumerate(evaluations):
                    if cost < worst:
                        worst = cost
                    if cost < 0:
                        iters.append(i+1)
                        violated = True
                        falsified += 1
                        break
                if not violated:
                    iters.append(len(evaluations))
                infeasible_iters.append(0)
                tot_generation_time += run["run_generation_time"]
                tot_simulation_time += run["run_simulation_time"]



        mean_infeasible_iter = np.mean(np.array(infeasible_iters))
        median_infeasible_iter = np.median(np.array(infeasible_iters))
        mean_fals_iter = np.mean(np.array(iters))
        std_fals_iter = np.std(np.array(iters))
        median_fals_iter = np.median(np.array(iters))
        lim_results[exp] = dict(falsified=falsified,
                                worst=worst,
                                mean_fals_iters=mean_fals_iter,
                                std_fals_iters=std_fals_iter,
                                median_fals_iters=median_fals_iter,
                                mean_infeasible_iters=mean_infeasible_iter,
                                mean_infeasible_iters_rate=mean_infeasible_iter/mean_fals_iter,
                                median_infeasible_iters=median_infeasible_iter)
        if exp == "staliro_unconstrained":
            lim_results[exp]["feasible_solutions"] = unconstr_feasible

        if exp in ["isotropic", "uniform_sta"]:
            lim_results[exp]['tot_generation_time'] = tot_generation_time
            lim_results[exp]['tot_simulation_time'] = tot_simulation_time

    results[l] = lim_results

for exp in experiments:
    print(f"{exp}: {results[500][exp]}")

with open(f"{result_dump_path}/results.json", "w+") as f:
    json.dump(obj=results[500], fp=f, indent=2, sort_keys=True)

'''for l in limits:
    print(f"\n==========\nLimit: {l}")
    for exp in experiments:
        if exp == "staliro_unconstrained":
            print(f"\t{exp}: Fals: {results[l][exp][0]} "
                  f"- Feasible: {results[l][exp][1]} "
                  f"\t{(f'(minimum: {results[l][exp][2]})') if results[l][exp][0] == 0 else ''} "
                  f"\tMean: {results[l][exp][3]:.1f}"
                  f"\tMedian: {results[l][exp][4]:.1f}")
        else:
            print(f"\t{exp}: Fals: {results[l][exp][0]} \t{(f'(minimum: {results[l][exp][1]})') if results[l][exp][0] == 0 else ''}"
                  f"\tMean: {results[l][exp][2]:.1f}"
                  f"\tMedian: {results[l][exp][3]:.1f}")'''
