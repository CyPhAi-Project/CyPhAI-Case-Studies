from datetime import timedelta
import plotly.graph_objects as go

from staliro import Trace, optimizers, staliro
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim
from simglucose_simobj import PATIENT_NAMES, build_sim_obj


def simglucose_wrapper(inputs: Blackbox.Inputs) -> Trace:
    patient_name = PATIENT_NAMES[0]
    meals = [
        (inputs.static["breakfast_time"], inputs.static["breakfast_size"]),
        (inputs.static["snack1_time"], inputs.static["snack1_size"]),
        (inputs.static["lunch_time"], inputs.static["lunch_size"]),
        (inputs.static["snack2_time"], inputs.static["snack2_size"]),
        (inputs.static["dinner_time"], inputs.static["dinner_size"]),
        (inputs.static["snack3_time"], inputs.static["snack3_size"]),
    ]
    sim_obj = build_sim_obj(meals, patient_name)
    trace = sim(sim_obj)

    # Shift time stamps and scale to minutes
    timepoints = (trace.index - trace.index[0]) / timedelta(minutes=1)
    return Trace(times=timepoints, states=trace.values)


optimizer = optimizers.DualAnnealing()

BG = "BG"
BG_COL = 0
requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
spec = rtamt.parse_dense(requirement, {BG: BG_COL})
options = TestOptions(
    runs=1,
    iterations=10,
    tspan=(0.0, 1000.0),
    static_inputs={
        # Meal times and sizes defined for RandomScenario in simglucose
        # Bound on meal size is (mu-3*sigma, mu+3*sigma)
        "breakfast_time": (5, 9), "breakfast_size": (45-3*10, 45+3*10),
        "snack1_time": (9, 10), "snack1_size": (10-3*5, 10+3*5),
        "lunch_time": (10, 14), "lunch_size": (70-3*10, 70+3*10),
        "snack2_time": (14, 16), "snack2_size": (10-3*5, 10+3*5),
        "dinner_time": (16, 20), "dinner_size": (80-3*10, 80+3*10),
        "snack3_time": (20, 23), "snack3_size": (10-3*5, 10+3*5),
    })

blackbox_obj = blackbox(simglucose_wrapper, step_size=1.0)

runs = staliro(
    blackbox_obj, spec, optimizer, options)

run = runs[0]

figure = go.Figure()
figure.update_layout(xaxis_title="time (min)", yaxis_title=BG)
figure.add_hline(y=70, line_color="red")
figure.add_hline(y=350, line_color="red")

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

figure.write_image("out/bg.jpeg")
