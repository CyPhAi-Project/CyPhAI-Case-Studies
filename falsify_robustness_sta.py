from datetime import timedelta
from typing import Callable

import plotly.graph_objects as go

from staliro import Trace, optimizers, staliro
from staliro.models import blackbox, Blackbox
from staliro.specifications import rtamt
from staliro.options import TestOptions

from simglucose.simulation.sim_engine import sim
from simglucose_simobj import PATIENT_NAMES, build_sim_obj
from sta.build_automaton_simplified import build_sa
from sta.generate_meals import build_meals_simplified
from sta.input_generator import InputGenerator

NUM_MEALS = 10

'''sta = build_sa()
sta_input_generator: InputGenerator = InputGenerator(
        sta, STA_OUT_FNAME, "sta/lib/wordgen",
        length=NUM_MEALS,
        postprocessing_fun=build_meals_simplified
    )

meal_plans = []
n_var = len(sta_input_generator.sta.var_names)
for _ in range(100):
    r = np.random.rand(NUM_MEALS*(2+n_var))
    meal_plan: dict[str, float] = dict()
    for i in range(1, NUM_MEALS + 1):
        start_idx = (i-1)*(2+n_var)
        meal_plan[f"delay_{i}"] = float(r[start_idx])
        meal_plan[f"transition_{i}"] = float(r[start_idx+1])
        for j in range(1, n_var + 1):
            meal_plan[f"{sta_input_generator.sta.var_names[j-1]}_{i}"] = float(r[start_idx + 1 + j])
    meals = sta_input_generator.generate_from_dict(meal_plan)
    meal_plans.append(meals)'''



def build_wrapper(input_generator: InputGenerator, patient_name) -> Callable[[Blackbox.Inputs], Trace]:
    def simglucose_wrapper(inputs: Blackbox.Inputs) -> Trace:
        # we assume the input is a dictionary like
        # { "delay_1": <value>, "transition_1": <value>, "var1_1": value, ..., "varK_1": value,
        #   "delay_2": <value>, "transition_2": <value>, "var1_2": value, ..., "varK_2": value,
        # ... }
        # So, for each transition, we have
        # 1) the value in [0,1] used to choose the delay
        # 2) the value in [0,1] used to choose the transition
        # 3) for each symbolic variable, the value in [0,1] used to generate its value


        meals = input_generator.generate_from_dict(inputs.static)
        print(meals)
        sim_obj = build_sim_obj(meals, patient_name, sim_time_days=1)
        trace = sim(sim_obj)

        # Shift time stamps and scale to minutes
        timepoints = (trace.index - trace.index[0]) / timedelta(minutes=1)
        return Trace(times=timepoints, states=trace.values)

    return simglucose_wrapper


# ALL THIS EXCEPT FOR STA MUST BE FIELDS OF sta
sta = build_sa()
STA_OUT_FNAME = "sta/output/sta_product.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/concrete_trajectories.json"

sta_input_gen: InputGenerator = InputGenerator(
            sta, STA_OUT_FNAME,"sta/lib/wordgen",
            length=NUM_MEALS,
            postprocessing_fun=build_meals_simplified
        )

optimizer = optimizers.DualAnnealing(min_cost=0.0)

blackbox_function = build_wrapper(sta_input_gen,PATIENT_NAMES[10])

n_var = len(sta_input_gen.sta.var_names)

search_space: dict[str, tuple[float, float]] = dict()
for i in range(1, NUM_MEALS + 1):
    start_idx = (i-1)*(2+n_var)
    search_space[f"delay_{i}"] = (0, 1)
    search_space[f"transition_{i}"] = (0, 1)
    for j in range(1, n_var + 1):
        search_space[f"{sta_input_gen.sta.var_names[j-1]}_{i}"] = (0, 1)



BG = "BG"
BG_COL = 0
requirement = f"always ({BG} > 70.0 and {BG} < 350.0)"
spec = rtamt.parse_dense(requirement, {BG: BG_COL})
options = TestOptions(
    runs=1,
    iterations=12,
    tspan=(0.0, 2880.0),
    static_inputs=search_space)


blackbox_obj = blackbox(blackbox_function, step_size=1.0)

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

figure.write_image("out/bg.jpeg")
