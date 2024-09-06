import os
import sys
sys.path.insert(0, '..')

from simglucose.simulation.sim_engine import sim
from simglucose_simobj import PATIENT_NAMES, build_sim_obj
import yaml

if __name__ == '__main__':

    with open('simglucose_cfg.yml', 'r') as file:
        cfg = yaml.safe_load(file)


    patient_name = PATIENT_NAMES[int(cfg['patient']['value'])]
    meals = [
        (cfg['meal']['breakfast_time']['value'],cfg['meal']['breakfast_size']['value']),
        (cfg['meal']['snack1_time']['value'],cfg['meal']['snack1_size']['value']),
        (cfg['meal']['lunch_time']['value'],cfg['meal']['lunch_size']['value']),
        (cfg['meal']['snack2_time']['value'],cfg['meal']['snack2_size']['value']),
        (cfg['meal']['dinner_time']['value'],cfg['meal']['dinner_size']['value']),
        (cfg['meal']['snack3_time']['value'],cfg['meal']['snack3_size']['value']),
    ]

    sim_obj = build_sim_obj(meals, patient_name)
    trace = sim(sim_obj)

    trace.to_csv('trace.csv')