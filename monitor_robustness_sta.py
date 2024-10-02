import sys
from datetime import timedelta
from typing import Literal
from pandas import DataFrame

from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.controller.pid_ctrller import PIDController
from simglucose.simulation.sim_engine import batch_sim
import stlrom

from simglucose_simobj import PATIENT_NAMES, build_sim_obj, FoxPIDController, FOXPID_PARAMS
from sta.generate_meals import generate_meals

NUM_SCENARIOS = 1

def batch_simglucose() -> list[DataFrame]:

    # Define meals as a list of tuples (time, meal_size) where time is the hour in a day in 24-hour format.

    meal_plans, sta_input_generator = generate_meals(NUM_SCENARIOS)
    sta_input_generator.to_file(meal_plans, "out/meal_plans.json")

    # meals = [(7, 45), (12, 70), (16, 15), (18, 80), (23, 10)]


    sim_obj_list = []
    for patient_name in PATIENT_NAMES:
        try:
            # Build controller
            sel_ctrl = "FoxPID"  # type: Literal["BB", "PID", "FoxPID"]
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
                    controller=ctrl))
        except KeyError:
            print(f"cannot find PID params for patient {patient_name}")

    # Batch simulation
    return batch_sim(sim_obj_list, parallel=True)


def main():
    bg = "BG"
    sim_results = batch_simglucose()

    end_time = 1400  # minutes

    # Robust monitoring
    stl_monitor = stlrom.STLDriver()
    # Spec from "Towards a verified artificial pancreas: Challenges and solutions for runtime verification.", RV 2015
    spec = f"""
    signal {bg}

    safety := alw_[0, {end_time}] (({bg}[t] > 70) and ({bg}[t] < 350))
    """
    # parse the formulas
    succ = stl_monitor.parse_string(spec)
    if not succ:
        print("Error when parsing STL spec formula")
        return

    patient_id = 0
    item_iter = sim_results[patient_id][bg].items()
    # Get the initial time stamp and value
    t0, v0 = next(item_iter)  # type: ignore
    stl_monitor.add_sample([0.0, v0])

    for t_datetime, value in item_iter:
        t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
        stl_monitor.add_sample([t, value])

    print("Robustness Interval:", stl_monitor.get_online_rob("safety", 0.0))


if __name__ == "__main__":
    main()
