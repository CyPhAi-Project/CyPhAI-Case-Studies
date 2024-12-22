from datetime import timedelta
from typing import *

import numpy as np
import stlrom
from apricopt.solving.blackbox.BlackBox import BlackBox
from simglucose.simulation.sim_engine import sim

from params import get_meal_space, get_whole_space
from simglucose_simobj import build_sim_obj
from utils import get_penalties, get_penalties_names, get_random_meal_plan


class SimGlucoseBlackBox(BlackBox):
    def __init__(self,
                 patient_name,
                 horizon: int,
                 dist_factor: float):
        super().__init__()
        self.patient_name = patient_name
        self.horizon: int = horizon
        self.bg = "BG"
        self.dist_factor: float = dist_factor



        self.bounds = get_whole_space(dist_factor) #get_meal_space(dist_factor)
        # self.bounds["snack_choice"] = (0, 2)
        self.history = []
        self.iteration = -1



    def _evaluate_robustness(self, sim_result) -> float:
        # Robust monitoring
        self.stl_monitor = stlrom.STLDriver()
        # Spec from "Towards a verified artificial pancreas: Challenges and solutions for runtime verification.", RV 2015
        self.spec = f"""
                    signal {self.bg}

                    safety := alw_[0, {self.horizon}] (({self.bg}[t] > 70) and ({self.bg}[t] < 350))
                    """
        # parse the formulas
        succ = self.stl_monitor.parse_string(self.spec)
        if not succ:
            print("Error when parsing STL spec formula")
            return

        item_iter = sim_result[self.bg].items()
        # Get the initial time stamp and value
        t0, v0 = next(item_iter)  # type: ignore
        self.stl_monitor.add_sample([0.0, v0])

        for t_datetime, value in item_iter:
            t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
            self.stl_monitor.add_sample([t, value])

        robustness_interval = self.stl_monitor.get_online_rob("safety", 0.0)
        print("Robustness Interval:", robustness_interval)
        return robustness_interval[1]





    def evaluate(self, parameters: Dict[str, float], check_input=True) -> Dict[str, float]:
        meals = [
            (parameters["breakfast_time"], parameters["breakfast_size"]),
            (parameters["snack1_time"], parameters["snack1_size"]),
            (parameters["lunch_time"], parameters["lunch_size"]),
            (parameters["snack2_time"], parameters["snack2_size"]),
            (parameters["dinner_time"], parameters["dinner_size"]),
            (parameters["snack3_time"], parameters["snack3_size"]),
        ]
        penalties = get_penalties(get_meal_space(self.dist_factor), parameters)

        result = {p_name: p_value for p_name, p_value in penalties.items() if p_name != "total"}
        if penalties["total"] > 0:
            infeasible = True
        else:
            infeasible = False

        sim_obj = build_sim_obj(meals, self.patient_name, sim_time_minutes=self.horizon)
        sim_result = sim(sim_obj)

        robustness = self._evaluate_robustness(sim_result)
        result["robustness"] = robustness if not infeasible else self.get_objective_upper_bound()
        result["falsifies"] = robustness

        self.iteration += 1
        self.history.append(
                dict(iteration=self.iteration,
                     cost=robustness,
                     violated=True if robustness<0 else False,
                     feasible=not infeasible))

        return result


    def evaluate_np_array(self, parameters: np.array, check_input=False) -> Dict[str, float]:
        raise NotImplementedError

    def evaluate_objective_np_array(self, parameters: np.array, check_input=False) -> float:
        raise NotImplementedError()

    def is_input_valid(self, parameters: Dict[str, float]) -> bool:
        return True

    def get_optimization_parameters_number(self) -> int:
        return len(self.get_optimization_parameters_ids())

    def get_optimization_parameters_ids(self) -> List[str]:
        return ["breakfast_time", "breakfast_size",
                "snack1_time", "snack1_size",
                "lunch_time", "lunch_size",
                "snack2_time", "snack2_size",
                "dinner_time", "dinner_size",
                "snack3_time", "snack3_size"]

    def get_optimization_parameter_lower_bound(self, param_id) -> float:
        return self.bounds[param_id][0]

    def get_optimization_parameter_upper_bound(self, param_id) -> float:
        return self.bounds[param_id][1]

    def get_optimization_parameters_lower_bounds_nparray(self) -> np.array:
        return np.array([self.get_optimization_parameter_lower_bound(p_id) for p_id in self.get_optimization_parameters_ids() ])

    def get_optimization_parameters_upper_bounds_nparray(self) -> np.array:
        return np.array(
            [self.get_optimization_parameter_upper_bound(p_id) for p_id in self.get_optimization_parameters_ids()])

    def _initial_meal(self):
        '''return {
            "breakfast_time": 7.5, "breakfast_size": 45,
            "snack1_time": 10, "snack1_size": 10,
            "lunch_time": 13, "lunch_size": 70,
            "snack2_time": 15.5, "snack2_size": 10,
            "dinner_time": 18.5, "dinner_size": 80,
            "snack3_time": 21, "snack3_size": 10,
            #"snack_choice": 2
        }'''
        return get_random_meal_plan(self.dist_factor)

    def get_optimization_parameter_initial_value(self, param_id) -> float:
        return self._initial_meal()[param_id]
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
        return 0 if param_id != "snack_choice" else 1.0
        '''if "time" in param_id:
            return 0.01
        else:
            return 0.1'''

    def get_extreme_barrier_constraints_number(self) -> int:
        return len(self.get_extreme_barrier_constraints_ids())
        #return 1

    def get_progressive_barrier_constraints_number(self) -> int:
        return 1
        #return 3

    def get_progressive_barrier_constraints_ids(self) -> List[str]:
        return ["falsifies"]
        #return ["breakfast_to_lunch_distance", "lunch_to_dinner_distance", "falsifies"]

    def get_extreme_barrier_constraints_ids(self) -> List[str]:
        return get_penalties_names()
        #return ["breakfast_to_lunch_distance", "lunch_to_dinner_distance"]
        #return ["at_least_one_snack", "breakfast_to_lunch_distance", "lunch_to_dinner_distance"]
        # return ["at_least_one_snack"]

    def get_objective_id(self) -> str:
        return "robustness"

    def get_objective_upper_bound(self) -> float:
        return 1000

    @staticmethod
    def get_raisable_exception_type():
        return ValueError

    def finalize(self) -> None:
        pass

