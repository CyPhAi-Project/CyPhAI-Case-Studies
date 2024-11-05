import json
from typing import List, Tuple, Callable, Any, Dict

import numpy as np
from staliro.models import Blackbox
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton


def identity_input_gen(self, traj): pass


class InputGenerator:

    def __init__(self, sta: SymbolicTimedAutomaton, sta_out_filename: str, wordgen_path,
                 length: int,
                 postprocessing_fun: Callable[[Any], List[Tuple[float, List[float]]]] = identity_input_gen):
        self.sta = sta
        self.length = length
        self.sta_out_filename = sta_out_filename
        self.wordgen_path = wordgen_path
        with open(sta_out_filename, "w+") as w:
            w.write(self.sta.prism)
        with open(f"{sta_out_filename}.constraints", "w+") as w:
            w.write(self.sta.prism_with_constraints)

        self.postprocess = postprocessing_fun

    def generate_uniform(self, abstract_traj_file: str, concrete_traj_file: str,
                         n: int = 1, length=None, initial_values: Dict[str, float] = None) \
            -> List[List[Tuple[float, List[float]]]]:
        traj_length: int = self.length
        if length:
            traj_length = length

        # Generate abstract trajectories with Wordgen'''
        abstract_trajectories = self._generate_abstract_trajectories(n, traj_length, abstract_traj_file)

        # Generate concrete trajectories by sampling symbolic constraints
        concrete_trajectories = self.sta.concretize_abstract_trajectories_uniform(
            abstract_trajectories=abstract_trajectories,
            initial_values=initial_values,
            concrete_trajectories_out_filename=concrete_traj_file
        )

        inputs = [self.postprocess(ct) for ct in concrete_trajectories]

        return inputs

    def to_file(self, concrete_trajectories, out_filename):
        with open(out_filename, "w+") as w:
            json.dump(concrete_trajectories, w, indent=4)

    def generate_uniform_to_file(self, out_traj_file: str, abstract_traj_file: str, concrete_traj_file,
                                 n: int = 1, length: int = None):
        inputs = self.generate_uniform(abstract_traj_file, concrete_traj_file, n, length)
        inputs_filename = out_traj_file
        with open(inputs_filename, "w+") as w:
            json.dump(inputs, w, indent=4)

    def _generate_abstract_trajectories(self, n, length, abstract_traj_file):
        # print(f"\n\n======================\nGenerating abstract trajectories with Wordgen")
        self.sta.wg_generate_random_abstract_trajectories(
            wordgen_path=self.wordgen_path,
            sta_filename=self.sta_out_filename,
            trajectories_to_generate=n,
            trajectory_length=length,
            abstract_trajectories_filename=abstract_traj_file
        )

        with open(abstract_traj_file, "r") as traj_file:
            abstr_trajectories = json.load(traj_file)
        return abstr_trajectories

    '''def dict_to_hypercube_pnt(self, ) -> np.ndarray:
        # we assume the input is a dictionary like
        # { "delay_1": <value>, "transition_1": <value>, "var1_1": value, ..., "varK_1": value,
        #   "delay_2": <value>, "transition_2": <value>, "var1_2": value, ..., "varK_2": value,
        # ... }
        # So, for each transition, we have
        # 1) the value in [0,1] used to choose the delay
        # 2) the value in [0,1] used to choose the transition
        # 3) for each symbolic variable, the value in [0,1] used to generate its value

        pnt = []
        for i in range(1, self.length + 1):
            pnt += [inputs.static[f"delay_{i}"]]
            pnt += [inputs.static[f"transition_{i}"]]
            for v in self.sta.var_names:
                pnt += [inputs.static[f"{v}_{i}"]]

        return np.array(pnt)'''

    def generate_from_dict(self, inputs: dict[str, float]):
        if self.length != len(inputs) / (2 + len(self.sta.var_names)):
            raise ValueError(
                f"Not enough values provided. Need {self.length * (2 + len(self.sta.var_names))} in [0, 1].")
        raw_trajectory = []
        for i in range(1, self.length + 1):
            delay = inputs[f"delay_{i}"]
            trans = inputs[f"transition_{i}"]
            var_values = np.array([inputs[f"{v}_{i}"] for v in self.sta.var_names])
            step = dict(delay=delay, transition=trans, var_values=var_values)
            raw_trajectory += [step]

        trajectory = self.sta.generate_from_raw_trajectory(self.wordgen_path, self.sta_out_filename,
                                                           raw_trajectory)
        result = self.postprocess(trajectory)
        return result
