import random
from typing import *

import numpy as np
from apricopt.solving.blackbox.BlackBox import BlackBox
from simglucose.simulation.sim_engine import sim

from symbolic_timed_automata.simglucose.simglucose_simobj import build_sim_obj
from symbolic_timed_automata.lib.syma.syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.simglucose.utils import evaluate_robustness


class SimGlucoseSTABlackBox(BlackBox):

    def __init__(self,
                 input_generator: InputGenerator,
                 patient_name,
                 horizon,
                 num_meals):
        super().__init__()
        self.input_generator = input_generator
        self.patient_name = patient_name
        self.horizon: int = horizon
        self.num_meals: int = num_meals
        self.bg = "BG"
        self.history = []
        self.iteration = -1

        n_var = len(self.input_generator.sta.var_names)

        self._opt_var_names: list[str] = []

        self.search_space: dict[str, tuple[float, float]] = dict()
        for i in range(1, self.num_meals + 1):
            del_var = f"delay_{i}"
            self._opt_var_names.append(del_var)
            trans_var = f"transition_{i}"
            self._opt_var_names.append(trans_var)
            self.search_space[del_var] = (0, 1)
            self.search_space[trans_var] = (0, 1)
            for j in range(1, n_var + 1):
                sym_var = f"{self.input_generator.sta.var_names[j - 1]}_{i}"
                self.search_space[sym_var] = (0, 1)
                self._opt_var_names.append(sym_var)
        self.initial_meal = None
        self.set_random_initial_values()

    def set_random_initial_values(self) -> None:
        self.initial_meal = dict()
        for param_id in self.get_optimization_parameters_ids():
            self.initial_meal[param_id] = round(random.uniform(0, 1),2)

    def evaluate(self, parameters: Dict[str, float], check_input=True) -> Dict[str, float]:
        # meals = self.input_generator.generate_from_dict(parameters)
        meals = self.input_generator.generate_from_point_in_hypercube(parameters)

        result = {}
        sim_obj = build_sim_obj(meals, self.patient_name, sim_time_minutes=self.horizon)
        sim_result = sim(sim_obj)

        robustness = evaluate_robustness(sim_result, self.bg, self.horizon)
        result["robustness"] = robustness
        result["falsifies"] = robustness
        self.iteration += 1
        self.history.append(dict(iteration=self.iteration, cost=robustness, violated=True if robustness<0 else False))
        return result


    def evaluate_np_array(self, parameters: np.array, check_input=False) -> Dict[str, float]:
        raise NotImplementedError

    def evaluate_objective_np_array(self, parameters: np.array, check_input=False) -> float:
        raise NotImplementedError()

    def is_input_valid(self, parameters: Dict[str, float]) -> bool:
        return True

    def get_optimization_parameters_number(self) -> int:
        return len(self.search_space)

    def get_optimization_parameters_ids(self) -> List[str]:
        return self._opt_var_names

    def get_optimization_parameter_lower_bound(self, param_id) -> float:
        return 0.0

    def get_optimization_parameter_upper_bound(self, param_id) -> float:
        return 1.0

    def get_optimization_parameters_lower_bounds_nparray(self) -> np.array:
        return np.array([self.get_optimization_parameter_lower_bound(p_id) for p_id in self.get_optimization_parameters_ids() ])

    def get_optimization_parameters_upper_bounds_nparray(self) -> np.array:
        return np.array(
            [self.get_optimization_parameter_upper_bound(p_id) for p_id in self.get_optimization_parameters_ids()])

    '''def _initial_meal(self):
        return {'delay_1': 0.56, 'delay_2': 0.5, 'delay_3': 0.45, 'delay_4': 0.75, 'delay_5': 0.0, 'delay_6': 0.0,
         'm_1': 0.55, 'm_2': 0.45, 'm_3': 0.21, 'm_4': 0.46, 'm_5': 0.15, 'm_6': 0.5,
         'transition_1': 0.04, 'transition_2': 0.0, 'transition_3': 0.74, 'transition_4': 0.45, 'transition_5': 0.0,
                'transition_6': 0.0}
         #return { var_name: 0.5 for var_name in self.get_optimization_parameters_ids() }'''

    def get_optimization_parameter_initial_value(self, param_id) -> float:
        return self.initial_meal[param_id]
        # return (self.get_optimization_parameter_lower_bound(param_id)
        # + self.get_optimization_parameter_upper_bound(param_id)) /2

    def optimization_parameters_initial_values_are_empty(self) -> bool:
        return False

    def set_optimization_parameters_initial_values(self, param_values: Dict[str, float]) -> None:
        raise NotImplementedError()

    def granularity_is_required(self) -> bool:
        return True

    def set_granularity_is_required(self, is_required: bool) -> None:
        pass

    def get_optimization_parameter_granularity(self, param_id) -> float:
        return 0.01

    def get_extreme_barrier_constraints_number(self) -> int:
        return 0
        #return 1

    def get_progressive_barrier_constraints_number(self) -> int:
        return 1
        #return 3

    def get_progressive_barrier_constraints_ids(self) -> List[str]:
        return ["falsifies"]

    def get_extreme_barrier_constraints_ids(self) -> List[str]:
        return []

    def get_objective_id(self) -> str:
        return "robustness"

    def get_objective_upper_bound(self) -> float:
        return 1000

    @staticmethod
    def get_raisable_exception_type():
        return ValueError

    def finalize(self) -> None:
        pass

