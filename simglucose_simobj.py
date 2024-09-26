from collections.abc import Callable, Generator
from datetime import datetime, timedelta
from typing import Literal, Sequence, Tuple, Union, get_args

from simglucose.actuator.pump import InsulinPump
from simglucose.controller.base import Action as ControlAction, Controller
from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.patient.t1dpatient import T1DPatient
from simglucose.sensor.cgm import CGMSensor
from simglucose.simulation.env import T1DSimEnv
from simglucose.simulation.scenario import Action as ScenarioAction, Scenario, CustomScenario
from simglucose.simulation.sim_engine import SimObj


TIME_TYPE = Union[int, float, timedelta, datetime]

# See Name column in params/vpatient_params.csv
PATIENT_TYPE = Literal[
    "child#001", "child#002",  "child#003", "child#004",  "child#005", "child#006", "child#007", "child#008", "child#009", "child#010",
    "adolescent#001", "adoldescent#002",  "adolescent#003", "adolescent#004",  "adolescent#005", "adolescent#006", "adolescent#007", "adolescent#008", "adolescent#009", "adolescent#010",
    "adult#001", "adult#002",  "adult#003", "adult#004",  "adult#005", "adult#006", "adult#007", "adult#008", "adult#009", "adult#010"
]
PATIENT_NAMES = get_args(PATIENT_TYPE)

FOXPID_PARAMS = {
    'child#001': [-3.49E-05,-1.00E-07,-1.00E-03],
    'child#002': [-3.98E-05,-2.87E-08,-3.98E-03],
    'child#003': [-6.31E-05,-1.74E-08,-1.00E-03],
    'child#004': [-6.31E-05,-1.00E-07,-1.00E-03],
    'child#005': [-1.00E-04,-2.87E-08,-6.31E-03],
    'child#006': [-3.49E-05,-1.00E-07,-1.00E-03],
    'child#007': [-3.98E-05,-6.07E-08,-2.51E-03],
    'child#008': [-3.49E-05,-3.68E-08,-1.00E-03],
    'child#009': [-3.49E-05,-1.00E-07,-1.00E-03],
    'child#010': [-4.54E-06,-3.68E-08,-2.51E-03],
    'adolescent#001': [-1.74E-04,-1.00E-07,-1.00E-02],
    'adolescent#002': [-1.00E-04,-1.00E-07,-6.31E-03],
    'adolescent#003': [-1.00E-04,-1.00E-07,-3.98E-03],
    'adolescent#004': [-1.00E-04,-1.00E-07,-4.79E-03],
    'adolescent#005': [-6.31E-05,-1.00E-07,-6.31E-03],
    'adolescent#006': [-4.54E-10,-1.58E-11,-1.00E-02],
    'adolescent#007': [-1.07E-07,-6.07E-08,-6.31E-03],
    'adolescent#008': [-4.54E-10,-4.54E-12,-1.00E-02],
    'adolescent#009': [-6.31E-05,-1.00E-07,-3.98E-03],
    'adolescent#010': [-4.54E-10,-4.54E-12,-1.00E-02],
    'adult#001': [-1.58E-04,-1.00E-07,-1.00E-02],
    'adult#002': [-3.98E-04,-1.00E-07,-1.00E-02],
    'adult#003': [-4.54E-10,-1.00E-07,-1.00E-02],
    'adult#004': [-1.00E-04,-1.00E-07,-3.98E-03],
    'adult#005': [-3.02E-04,-1.00E-07,-1.00E-02],
    'adult#006': [-2.51E-04,-2.51E-07,-1.00E-02],
    'adult#007': [-1.22E-04,-3.49E-07,-2.87E-03],
    'adult#008': [-1.00E-04,-1.00E-07,-1.00E-02],
    'adult#009': [-1.00E-04,-1.00E-07,-1.00E-02],
    'adult#010': [-1.00E-04,-1.00E-07,-1.00E-02]}


# See Name column in params/pump_params.csv
PUMP_TYPE = Literal["Cozmo", "Insulet"]

# See Name column in params/sensor_params.csv
SENSOR_TYPE = Literal["Dexcom", "GuardianRT", "Navigator"]
# specify start_time as the beginning of today
START_TIME = datetime.combine(datetime.now().date(), datetime.min.time())
# Specify results saving path
RESULT_PATH = './out'


class FoxPIDController(Controller):
    def __init__(self, setpoint, kp, ki, kd, basal=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0
        self.previous_error = 0
        self.basal = basal
        self.setpoint = setpoint

    def policy(self, observation, reward, done, **kwargs):
        value=observation.CGM
        error = self.setpoint - value
        p_act = self.kp * error
        # print('p: {}'.format(p_act))
        self.integral += error
        i_act = self.ki * self.integral
        # print('i: {}'.format(i_act))
        d_act = self.kd * (error - self.previous_error)
        try:
            if self.basal is not None:
                b_act = self.basal
            else:
                b_act = 0
        except:
            b_act = 0
        # print('d: {}'.format(d_act))
        self.previous_error = error
        control_input = p_act + i_act + d_act + b_act
        action = ControlAction(basal=control_input, bolus=0)
        #print('error=', error,'A=',action)
        return action

    def reset(self):
        self.integral = 0
        self.previous_error = 0


class GenerativeScenario(Scenario):
    def __init__(self, start_time: datetime,
                 scen_gen_fun: Callable[[], Generator[Tuple[TIME_TYPE, ScenarioAction], None, None]]):
        '''
        scen_gen - a generator function yielding tuples (time, action), where time is a datetime or
                   timedelta or double, action is a namedtuple defined by
                   scenario.Action. When time is a timedelta, it is
                   interpreted as the time of start_time + time. Time in double
                   type is interpreted as time in timedelta with unit of hours
        '''
        Scenario.__init__(self, start_time=start_time)
        self._prev_itvl = (None, start_time)
        self._scen_gen_fun = scen_gen_fun
        self.reset()

    def get_action(self, t):
        assert t >= self._prev_itvl[0]
        try:
            raise NotImplementedError("TODO: Get meal size at a timepoint give the possibly infinite iterable.")
        except StopIteration:
            return ScenarioAction(meal=0)  # Return dummy meal after reaching the end of the iterable

    def reset(self):
        self._scen_iter = self._scen_gen_fun()  # Create a new generator


def build_sim_obj(
        meals: Sequence[Tuple[TIME_TYPE, float]],
        patient_name: PATIENT_TYPE,
        patient_init_state = None,
        patient_random_init_bg: bool = False,
        patient_seed = None,
        patient_t0: float = 0.0,
        sensor_name: SENSOR_TYPE = "Dexcom",
        sensor_seed: int = 1,
        pump_name: PUMP_TYPE = "Insulet",
        controller: Controller = BBController()) -> SimObj:
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
    scenario = CustomScenario(start_time=START_TIME, scenario=meals)
    env = T1DSimEnv(patient, sensor, pump, scenario)

    # Put them together to create a simulation object
    return SimObj(env, controller, timedelta(days=1), animate=False, path=RESULT_PATH)
