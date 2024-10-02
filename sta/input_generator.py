import json
from typing import List, Tuple, Callable, Any

from syma.automaton.automaton import SymbolicTimedAutomaton
from syma.volume.estimator import volume_estimate

from sta.utils import concretize_abstract_trajectories, wg_generate_abstract_trajectories, \
    build_constraints_abstractions, identity_input_gen


class InputGenerator:

    def __init__(self, sta: SymbolicTimedAutomaton, var_names, var_bounds, sta_out_filename: str, wordgen_path,
                 postprocessing_fun:Callable[[Any], List[Tuple[float, List[float]]]]=identity_input_gen):
        self.sta = sta
        self.var_names = var_names
        self.var_bounds = var_bounds
        self.volume_dict, self.abstraction_dict = volume_estimate(sta)

        self.sta_prism, self.constraints_mapping = sta.to_prism(self.volume_dict, visible_sym_constraints=False)
        self.sta_prism_constr, _ = sta.to_prism(self.volume_dict, visible_sym_constraints=True)
        self.sta_out_filename = sta_out_filename
        self.wordgen_path = wordgen_path
        with open(sta_out_filename, "w+") as w:
            w.write(self.sta_prism)
        with open(f"{sta_out_filename}.constraints", "w+") as w:
            w.write(self.sta_prism_constr)

        self.labels_to_abstractions, self.labels_to_formula, self.label_to_values = build_constraints_abstractions(
            self.constraints_mapping,
            self.abstraction_dict,
            self.var_names,
            self.var_bounds)
        self.postprocess = postprocessing_fun


    def generate(self, length:int, abstract_traj_file: str, concrete_traj_file:str, n:int=1) \
            -> List[List[Tuple[float, List[float]]]]:
        # Generate abstract trajectories with Wordgen'''
        abstract_trajectories = self._generate_abstract_trajectories(n, length, abstract_traj_file)

        # Generate concrete trajectories by sampling symbolic constraints
        concrete_trajectories = \
            concretize_abstract_trajectories(
                abstract_trajectories,
                self.var_names, self.labels_to_abstractions, self.labels_to_formula, self.label_to_values,
                initial_values=concrete_traj_file,
                concrete_trajectories_out_filename=concrete_traj_file
            )

        inputs = [self.postprocess(ct) for ct in concrete_trajectories]

        return inputs



    def to_file(self, concrete_trajectories, out_filename):
        with open(out_filename, "w+") as w:
            json.dump(concrete_trajectories, w, indent=4)
    def generate_to_file(self, out_traj_file: str, abstract_traj_file: str, concrete_traj_file, length: int, n:int=1):

        inputs = self.generate(length, abstract_traj_file, concrete_traj_file, n)
        inputs_filename = out_traj_file
        with open(inputs_filename, "w+") as w:
            json.dump(inputs, w, indent=4)


    def _generate_abstract_trajectories(self, n, length, abstract_traj_file):
        # print(f"\n\n======================\nGenerating abstract trajectories with Wordgen")

        wg_generate_abstract_trajectories(self.wordgen_path, self.sta_out_filename,
                                          n, length,
                                          abstract_traj_file)

        with open(abstract_traj_file, "r") as traj_file:
            abstr_trajectories = json.load(traj_file)
        return abstr_trajectories
