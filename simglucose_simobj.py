from datetime import datetime, timedelta
from typing import Literal, get_args

from simglucose.actuator.pump import InsulinPump
from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.sensor.cgm import CGMSensor
from simglucose.simulation.env import T1DSimEnv
from simglucose.simulation.scenario import CustomScenario
from simglucose.simulation.sim_engine import SimObj


# See Name column in params/vpatient_params.csv
PATIENT_TYPE = Literal[
    "adolescent#001", "adolescent#002",  "adolescent#003", "adolescent#004",  "adolescent#005", "adolescent#006", "adolescent#007", "adolescent#008", "adolescent#009", "adolescent#010",
    "adult#001", "adult#002",  "adult#003", "adult#004",  "adult#005", "adult#006", "adult#007", "adult#008", "adult#009", "adult#010",
    "child#001", "child#002",  "child#003", "child#004",  "child#005", "child#006", "child#007", "child#008", "child#009", "child#010"
]
PATIENT_NAMES = get_args(PATIENT_TYPE)


# See Name column in params/pump_params.csv
PUMP_TYPE = Literal["Cozmo", "Insulet"]

# See Name column in params/sensor_params.csv
SENSOR_TYPE = Literal["Dexcom", "GuardianRT", "Navigator"]
# specify start_time as the beginning of today
START_TIME = datetime.combine(datetime.now().date(), datetime.min.time())
# Specify results saving path
RESULT_PATH = './robustness'


def build_sim_obj(
        patient_name: PATIENT_TYPE,
        patient_init_state = None,
        patient_random_init_bg: bool = False,
        patient_seed = None,
        patient_t0: float = 0.0,
        sensor_name: SENSOR_TYPE = "Dexcom",
        sensor_seed: int = 1,
        pump_name: PUMP_TYPE = "Insulet",
        perturb: bool = False) -> SimObj:
    # Create a simulation environment
    patient = T1DPatient.withName(
        name=patient_name,
        init_state=patient_init_state,
        random_init_bg=patient_random_init_bg,
        seed=patient_seed,
        t0=patient_t0)
    sensor = CGMSensor.withName(sensor_name, seed=sensor_seed)
    pump = InsulinPump.withName(pump_name)

    # Custom scenario is a list of tuples (time, meal_size)
    scen = [(7, 45), (12, 70), (16, 15), (18, 80), (23, 10)]
    if perturb:
        # TODO
        scen.insert(5, (21, 0))
        scen.insert(3, (14, 0))
        scen.insert(1, (10, 0))
    scenario = CustomScenario(start_time=START_TIME, scenario=scen)
    env = T1DSimEnv(patient, sensor, pump, scenario)

    # Create a controller
    controller = BBController()

    # Put them together to create a simulation object
    return SimObj(env, controller, timedelta(days=1), animate=False, path=RESULT_PATH)
