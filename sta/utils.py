import os
import json
import argparse
from typing import List, Dict, Union, Tuple
import numpy as np


from syma.volume.hyperrectangle_abstraction import HyperrectangleAbstraction

from syma.volume.constraint_abstraction import ConstraintAbstraction


def get_command_line_arguments():
    parser = argparse.ArgumentParser(description="Syma + Wordgen constrainted trajectory generation")

    parser.add_argument('-n', '--number', type=int,
                        help="The number of trajectories to generate",
                        required=True)

    parser.add_argument('-l', '--length', type=int,
                        help="The length of trajectories in terms of number of events",
                        required=True)

    parser.add_argument('-o', '--dump', '--output', '--output-pattern', type=str, dest='output_pattern',
                        help="Pattern (path) of .mat files to store the generated trajectories, using Python's pattern format",
                        required=True)

    parser.add_argument('-c', '--concrete', '--concrete-out', type=str, dest='concrete',
                        help="Output path of the generated concrete trajectories, a json file", default=None,
                        required=True)

    parser.add_argument('-a', '--abstract', '--abstract-out', type=str, dest='abstract',
                        help="Output path of the generated abstract trajectories, a json file",
                        required=True)

    parser.add_argument('-s', '--sta', '--sta-out', type=str, dest='sta_out_filename',
                        help="Output path of the generated STA, in PRISM format",
                        required=True)

    parser.add_argument('-d', '--dt', type=float,
                        help="The time step for generated trajectories", default=0.001,
                        required=False)

    parser.add_argument('-w', '--wg', '--wordgen', '--wordgen-path',
                        type=str, dest="wordgen_path",
                        help="Path of Wordgen executable. If not specified, it is assumed to be in the PATH",
                        default="Wordgen", required=False)

    args = parser.parse_args()
    return args


def wg_generate_abstract_trajectories(wordgen_path:str,
                                      sta_filename: str,
                                      trajectories_to_generate: int,
                                      trajectory_length: int,
                                      abstract_trajectories_filename: str):
    # wordgen_exe = os.getenv("WORDGEN_EXE")
    os.environ["OCAMLRUNPARAM"] = "b"
    cmd = (f"{wordgen_path} {sta_filename} "
           f"--traj {trajectories_to_generate} "
           f"--receding {trajectory_length} "
           f"--exact-rational "
           f"--output-format  json {abstract_trajectories_filename}.broken")
    print(f"\n\nWordgen command:\n{cmd}")
    os.system(cmd)

    # Fix abstract trajectories file -------
    with open(abstract_trajectories_filename + ".broken", "r") as f:
        lines = f.readlines()

    to_write = []
    for l in lines:
        if '"final"' in l:
            to_write[-1] = to_write[-1][:-2]
            to_write.append("\n],\n")
        elif '[]' in l or l == "\n":
            continue
        else:
            to_write.append(l)
    to_write[-1] = to_write[-1][:-2] + "\n]\n"

    with open(abstract_trajectories_filename, "w") as f:
        f.writelines(to_write)

def build_constraints_abstractions(constraints_mapping, abstraction_dict, var_names, var_bounds,
                                   precision=1e-2, min_volume=1e-2) -> \
        Tuple[Dict[str, HyperrectangleAbstraction], Dict[str, str], Dict[str, Dict[str, float]]]:
    labels_to_hra: Dict[str, HyperrectangleAbstraction] = dict()
    labels_to_formula: Dict[str, str] = dict()
    for action, constraint_info in constraints_mapping.items():
        constraint, abstraction_type = constraint_info
        print(f"Computing abstraction of constraint {action}")
        # hra = HyperrectangleAbstraction(var_names, var_bounds, constraint,max_samples=10000)
        # hra.compute_abstraction(precision=precision, min_volume=min_volume)
        #labels_to_hra[f"SYM_CONSTR_{constr_num}"] = hra


        #abstraction: ConstraintAbstraction = abstraction_type(var_names, var_bounds, constraint)
        #abstraction.compute_abstraction()
        #labels_to_hra[f"SYM_CONSTR_{constr_num}"] = abstraction
        labels_to_hra[action] = abstraction_dict[constraint]


        labels_to_formula[action] = constraint.formula

    label_to_values: Dict[str, Dict[str, float]] = {}
    return labels_to_hra, labels_to_formula, label_to_values

def concretize_abstract_trajectories(abstract_trajectories: dict,
                                     var_names: List[str],
                                     label_to_abstraction: Dict[str, ConstraintAbstraction],
                                     label_to_formula: Dict[str, str],
                                     label_to_values: Dict[str, Dict[str, float]],  # to be reconsidered
                                     initial_values: Union[ConstraintAbstraction, Dict[str, float]],
                                     initial_formula=None,
                                     concrete_trajectories_out_filename=None):
    sym_timed_words = []

    print(f"\n\n======================\nGenerating concrete trajectories")
    for t in abstract_trajectories:
        word = []
        if isinstance(initial_values, ConstraintAbstraction):
            sample = initial_values.uniform_sample()
            values = {var_name: sample[i] for i, var_name in enumerate(var_names)}
            step = dict(delay=0.0, vars=values, constraint=initial_formula) if initial_formula \
                else dict(delay=0.0, vars=values)
            word += [step]
        elif isinstance(initial_values, dict):
            step = dict(delay=0.0, vars=initial_values)
            word += [step]

        for transition in t:
            if "action" not in transition:
                break
            action = transition["action"]
            if action in label_to_abstraction:
                abstr = label_to_abstraction[transition["action"]]
                sample = abstr.uniform_sample()
                values = {var_name: sample[i] for i, var_name in enumerate(var_names)}
                fml = str(label_to_formula[transition["action"]])
                step = dict(action=action, delay=transition["delay"], vars=values, constraint=fml)
            else:
                values = label_to_values[transition["action"]]
                step = dict(action=action, delay=transition["delay"], vars=values)

            word += [step]
        sym_timed_words += [word]

    if concrete_trajectories_out_filename:
        with open(concrete_trajectories_out_filename, "w+") as w:
            json.dump(sym_timed_words, w, indent=4)
    return sym_timed_words

def identity_input_gen(self):
    pass

def concretize_abstract_trajectories_with_POST(abstract_trajectories: dict,
                                     var_names: List[str],
                                     label_to_hra: Dict[str, HyperrectangleAbstraction],
                                     label_to_formula: Dict[str, str],
                                     label_to_values: Dict[str, Dict[str, float]],  # to be reconsidered
                                     initial_values: Union[HyperrectangleAbstraction, Dict[str, float]],
                                     initial_formula=None,
                                     concrete_trajectories_out_filename=None):
    timed_sym_words = []

    print(f"\n\n======================\nGenerating concrete trajectories")
    for t in abstract_trajectories:
        word = []
        if isinstance(initial_values, HyperrectangleAbstraction):
            sample = initial_values.uniform_sample()
            values = {var_name: sample[i] for i, var_name in enumerate(var_names)}
            step = dict(delay=0.0, vars=values, constraint=initial_formula) if initial_formula \
                else dict(delay=0.0, vars=values)
            word += [step]
        elif isinstance(initial_values, dict):
            step = dict(delay=0.0, vars=initial_values)
            word += [step]

        active_post_samples = dict()
        active_post_fml = dict()
        for transition in t:
            if "action" not in transition:
                break
            action = transition["action"]
            if action in label_to_hra:
                hra = label_to_hra[action]
                sample = hra.uniform_sample()
                values = {var_name: sample[i] for i, var_name in enumerate(var_names)}
                fml = str(label_to_formula[action])
                step = dict(delay=transition["delay"], vars=values, constraint=fml)
            elif "_PL_" in action:
                sym_constr_label = action.split("_PL_")[0]
                post_label = action.split("_PL_")[1]
                if "_PV_" in action:
                    # it is the first post call for the label
                    post_vars = action.split("_PV_")[1].split("_v_")
                    if post_label in active_post_samples:
                        raise RuntimeError("Previous POST not resolved yet!")
                    hra = label_to_hra[sym_constr_label]
                    sample = hra.uniform_sample()
                    values = {var_name: sample[i] for i, var_name in enumerate(var_names) if var_name not in post_vars}
                    postponed_values = {var_name: sample[i] for i, var_name in enumerate(var_names) if var_name in post_vars}
                    active_post_samples[post_label] = postponed_values
                    fml = str(label_to_formula[sym_constr_label])
                    active_post_fml[post_label] = fml
                    step = dict(delay=transition["delay"], vars=values, constraint=fml, post_label=post_label)
                else:
                    if post_label not in active_post_samples:
                        raise RuntimeError("POST not present!")
                    post_values = active_post_samples[post_label]
                    fml = active_post_fml[post_label]
                    step = dict(delay=transition["delay"], vars=post_values, constraint=fml, post_label=post_label)
                    del active_post_samples[post_label]
                    del active_post_fml[post_label]
            else:
                values = label_to_values[transition["action"]]
                step = dict(delay=transition["delay"], vars=values)
            word += [step]
        timed_sym_words += [word]

    if concrete_trajectories_out_filename:
        with open(concrete_trajectories_out_filename, "w+") as w:
            json.dump(timed_sym_words, w, indent=4)
    return timed_sym_words


import ppl

def random_direction(dim):
    """Generate a random direction on the n-dimensional unit sphere."""
    direction = np.random.normal(size=dim)
    direction /= np.linalg.norm(direction)
    return direction

def hit_and_run_sample(polytope, start, num_samples):
    """
    Generate random samples from a convex polytope defined by pplpy.

    Parameters:
    polytope (ppl.C_Polyhedron): The polytope defined using pplpy.
    start (np.ndarray): Starting point inside the polytope.
    num_samples (int): Number of samples to generate.

    Returns:
    np.ndarray: Array of shape (num_samples, n) containing the sampled points.
    """
    n = start.size
    samples = np.zeros((num_samples, n))
    samples[0] = start

    for i in range(1, num_samples):
        direction = random_direction(n)

        # Compute the step size in the positive and negative direction
        positive_bound = np.inf
        negative_bound = -np.inf

        for constraint in polytope.constraints():
            a = np.array([constraint.coefficient(ppl.Variable(j)) for j in range(n)], dtype=float)
            b = float(constraint.inhomogeneous_term())

            numer = b - np.dot(a, samples[i-1])
            denom = np.dot(a, direction)
            if denom > 0:
                positive_bound = min(positive_bound, numer / denom)
            elif denom < 0:
                negative_bound = max(negative_bound, numer / denom)

        # Sample a random step size within the feasible interval
        step_size = np.random.uniform(negative_bound, positive_bound)
        samples[i] = samples[i-1] + step_size * direction

    return samples
