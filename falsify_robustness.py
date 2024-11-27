from datetime import timedelta
import plotly.graph_objects as go

import numpy as np

from staliro import Trace, optimizers, staliro
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim
from simglucose_simobj import PATIENT_NAMES, build_sim_obj


np.random.seed(104)
NUM_MEALS = 5
PATIENT = PATIENT_NAMES[10]
MAX_OPT_ITERATIONS = 10
SIM_TIME_DAYS = 2
STL_TIME_SPAN = 30*60 # in minutes


def simglucose_wrapper(inputs: Blackbox.Inputs) -> Trace:
    patient_name = PATIENT
    meals = [
        (inputs.static["breakfast_time"], inputs.static["breakfast_size"]),
        (inputs.static["snack1_time"], inputs.static["snack1_size"]),
        (inputs.static["lunch_time"], inputs.static["lunch_size"]),
        (inputs.static["snack2_time"], inputs.static["snack2_size"]),
        (inputs.static["dinner_time"], inputs.static["dinner_size"]),
        # (inputs.static["snack3_time"], inputs.static["snack3_size"]),
    ]
    sim_obj = build_sim_obj(meals, patient_name, sim_time_days=SIM_TIME_DAYS)
    trace = sim(sim_obj)

    # Shift time stamps and scale to minutes
    timepoints = (trace.index - trace.index[0]) / timedelta(minutes=1)
    return Trace(times=timepoints, states=trace.values)


optimizer = optimizers.DualAnnealing(min_cost=1e-6)

DIST_FACTOR = 1.0

static_inputs={
        # Meal times and sizes defined for RandomScenario in simglucose
        # Bound on meal size is (mu-3*sigma, mu+3*sigma)
        "breakfast_time": (5, 9), "breakfast_size": (45-(3*10)*DIST_FACTOR, 45+(3*10)*DIST_FACTOR),
        "snack1_time": (9, 11), "snack1_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
        "lunch_time": (12, 15), "lunch_size": (70-(3*10)*DIST_FACTOR, 70+(3*10)*DIST_FACTOR),
        "snack2_time": (14, 16), "snack2_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
        "dinner_time": (16, 20), "dinner_size": (80-(3*10)*DIST_FACTOR, 80+(3*10)*DIST_FACTOR),
        "snack3_time": (20, 23), "snack3_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
    }

BG = "BG"
BG_COL = 0
requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
spec = rtamt.parse_dense(requirement, {BG: BG_COL})
options = TestOptions(
    runs=1,
    iterations=MAX_OPT_ITERATIONS,
    tspan=(0.0, STL_TIME_SPAN),
    static_inputs=static_inputs)

blackbox_obj = blackbox(simglucose_wrapper, step_size=1.0)

runs = staliro(
    blackbox_obj, spec, optimizer, options)

run = runs[0]

figure = go.Figure()
figure.update_layout(xaxis_title="time (min)", yaxis_title=BG)
figure.add_hline(y=70, line_color="red")
figure.add_hline(y=350, line_color="red")
res = [f"iteration {i+1} cost: {e.cost} {'== VIOLATED' if e.cost < 0 else ''}" for i, e in enumerate(run.evaluations)]
for s in res:
    print(s)


for i, ev in enumerate(run.evaluations):
    trace = ev.extra.trace
    figure.add_trace(
        go.Scatter(
            x=list(trace.times),
            y=[state[BG_COL] for state in trace.states],
            mode="lines",
            # line_color="green",
            name=f"{BG}{i}",
        )
    )

figure.write_image("out/falsification/naive_staliro/bg.jpeg")
