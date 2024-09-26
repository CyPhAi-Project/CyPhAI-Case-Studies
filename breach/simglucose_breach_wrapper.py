import os
import sys
sys.path.insert(0, '..')

from simglucose.simulation.sim_engine import sim
from simglucose_simobj import PATIENT_NAMES, build_sim_obj, FoxPIDController,FOXPID_PARAMS
from simglucose.controller.basal_bolus_ctrller import BBController
from simglucose.controller.pid_ctrller import PIDController

import yaml


def get_controller(cfg):
    target = cfg['controller']['target']['value']
    ctrl_id = cfg['controller']['type']['value'] 
    if ctrl_id==0:
        ctrl = BBController(target=target)  # Specify target BG
    elif ctrl_id==1:
        P = cfg['controller']['PID']['P']['value']
        I = cfg['controller']['PID']['I']['value']
        D = cfg['controller']['PID']['D']['value']
        print('using PID controller (P:',P, 'I:',I,'D:',D,')...')        
        ctrl = PIDController(P=P, I=I, D=D, target=target)
    elif ctrl_id==2:
        print('Using FoxPID...')
        kp, ki, kd = FOXPID_PARAMS[patient_name]
        ctrl = FoxPIDController(setpoint=112.517, kp=kp, ki=ki, kd=kd, basal=None)       
    
    return ctrl

def get_meals(cfg):

    meals = [
        (cfg['meal']['breakfast_time']['value'],cfg['meal']['breakfast_size']['value']),
        (cfg['meal']['snack1_time']['value'],cfg['meal']['snack1_size']['value']),
        (cfg['meal']['lunch_time']['value'],cfg['meal']['lunch_size']['value']),
        (cfg['meal']['snack2_time']['value'],cfg['meal']['snack2_size']['value']),
        (cfg['meal']['dinner_time']['value'],cfg['meal']['dinner_size']['value']),
        (cfg['meal']['snack3_time']['value'],cfg['meal']['snack3_size']['value']),
    ]
    return meals


if __name__ == '__main__':

    cfg_file = sys.argv[1]
    print('Reading cfg from ', cfg_file, '...')
    with open(cfg_file, 'r') as file:
        cfg = yaml.safe_load(file)
    
    
    patient_name = PATIENT_NAMES[int(cfg['patient']['value'])]
    ctrl = get_controller(cfg)
    meals = get_meals(cfg)

    sim_obj = build_sim_obj(meals=meals, patient_name=patient_name,  controller=ctrl)
    trace = sim(sim_obj)

    trace.to_csv(cfg['out'])