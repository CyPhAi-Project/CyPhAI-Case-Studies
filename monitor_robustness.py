from datetime import timedelta
from pandas import DataFrame

from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.controller.pid_ctrller import PIDController
from simglucose.simulation.sim_engine import batch_sim
import stlrom

from simglucose_simobj import PATIENT_NAMES, build_sim_obj


NUM_SCENARIOS = 1


def batch_simglucose() -> list[DataFrame]:
    perturb = True

    # Define meals as a list of tuples (time, meal_size) where time is the hour in a day in 24-hour format.
    meals = [(7, 45), (12, 70), (16, 15), (18, 80), (23, 10)]
    if perturb:
        # TODO different purterbation strategies
        meals.insert(5, (21, 0))  # add a dummy meal of size 0
        meals.insert(3, (14, 0))  # add a dummy meal of size 0
        meals.insert(1, (10, 0))  # add a dummy meal of size 0

    # Build controller
    pid_ctrl = True
    if pid_ctrl:
        ctrl = PIDController(P=0.001, I=0.00001, D=0.001, target=140)
    else:
        ctrl = BBController(target=140)  # Specify target BG

    # Create scenarios
    sim_obj_list = [build_sim_obj(
        meals=meals,
        patient_name=name,
        controller=ctrl
    ) for name in PATIENT_NAMES[:NUM_SCENARIOS]]

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

    item_iter = sim_results[0][bg].items()
    # Get the initial time stamp and value
    t0, v0 = next(item_iter)  # type: ignore
    stl_monitor.add_sample([0.0, v0])

    for t_datetime, value in item_iter:
        t = (t_datetime - t0) / timedelta(minutes=1)  # Shift time stamps and scale to minutes
        stl_monitor.add_sample([t, value])

    print("Robustness Interval:", stl_monitor.get_online_rob("safety", 0.0))


if __name__ == "__main__":
    main()
