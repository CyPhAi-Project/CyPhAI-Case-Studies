'''import enum

from staliro.models import Blackbox


class SimpleSystem:
    class Mode(enum.IntEnum):
        A = 1
        B = 2

    def __init__(self, initial_state: tuple[float, float], epsilon: float = 1e-1):
        self.x: float
        self.y: float
        self.x, self.y = initial_state
        self.mode = SimpleSystem.Mode.A
        self.epsilon = epsilon
        self.x_dot: float = 0.1
        self.y_dot: float = 0.1
        self.z = (self.x - 0.5) * (self.y - 0.5)

    def step(self, step_size: float):
        if self.mode is SimpleSystem.Mode.A and self.x + self.y >= 2:
            self.mode = SimpleSystem.Mode.B
            self.x_dot = -self.x_dot
            self.y_dot = -self.y_dot
        if self.mode is SimpleSystem.Mode.B and self.x + self.y <= 1:
            self.mode = SimpleSystem.Mode.A
            self.x_dot = -self.x_dot
            self.y_dot = -self.y_dot



        self.x, self.y = self.x + self.x_dot*self.x * step_size, self.y + self.y_dot*self.y * step_size
        self.z = (self.x - 0.5) * (self.y - 0.5)

from staliro import models, Sample, TestOptions
import plotly.graph_objects as go
STEP_SIZE = 0.1

#@models.model()
def run_system(inputs: models.Sample) -> models.Trace[list[tuple[float, float]]]:
    system = SimpleSystem((inputs.values[0], inputs.values[1]))
    states = {}

    for step in range(1000):
        time = step * STEP_SIZE
        states[time] = (system.x, system.y, system.z)
        system.step(STEP_SIZE)

    return models.Trace(states), states

xy0 = Sample((1.5, 1.1), opts=TestOptions())
trace, states = run_system(xy0)
print(states)

# Extract time, x, and y values
times = list(states.keys())
x_values = [point[0] for point in states.values()]
y_values = [point[1] for point in states.values()]
z_values = [point[2] for point in states.values()]

# Create the plot
fig = go.Figure()

# Add x trajectory
fig.add_trace(go.Scatter(
    x=times, y=x_values,
    mode='lines+markers',
    name='x trajectory'
))

# Add y trajectory
fig.add_trace(go.Scatter(
    x=times, y=y_values,
    mode='lines+markers',
    name='y trajectory'
))

# Add y trajectory
fig.add_trace(go.Scatter(
    x=times, y=z_values,
    mode='lines+markers',
    name='z trajectory'
))

# Update layout for better visualization
fig.update_layout(
    title='Trajectories of x and y over time',
    xaxis_title='Time',
    yaxis_title='Value',
    legend_title='Variable'
)

# Show the plot
fig.show()'''
import bisect
import random
import sys

import numpy as np
from scipy.integrate import solve_ivp
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.generation.input_generator import InputGenerator

from symbolic_timed_automata.ode.sta import build_ode_sta
STA_OUT_FNAME = "symbolic_timed_automata/ode/output/ode_sta.prism"
ABSTRACT_TRAJ_FNAME = "symbolic_timed_automata/ode/output/ode_sta_abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "symbolic_timed_automata/ode/output/ode_sta_concrete_trajectories.json"

SIGNAL_LENGTH = 100
TOT_N_SIGNALS = 10**0
N_WORDS_BATCH = 10**3
DEBUG = False


def build_system(inputs: dict[float, tuple[float, float]], gain:float = 10.0):

    # Define the system dynamics
    input_times: list[float] = list(inputs.keys())
    input_times.sort()

    def system(t, z):
        x1, x2 = z
        # Input functions (modify these to test different scenarios)
        '''if 1 < t < 1.4:
            u1 = 0.5  # Required value for y=0
            u2 = 0.5  # Required value for y=0
        else:
            u1 = 0.6  # Initial non-0.5 value
            u2 = 0.4  # Initial non-0.5 value'''


        closest_time: float = input_times[bisect.bisect_left(input_times, t)]
        u1, u2 = inputs[closest_time]

        dx1dt = gain * (u1 - 0.5) - gain * x1
        dx2dt = gain * (u2 - 0.5) - gain * x2
        return [dx1dt, dx2dt]
    return system


# Initial conditions and time span
z0 = [0.0, 0.0]
t_span = [0, 5]
t_eval = np.linspace(0, 5, 1000)

'''inputs: dict[float, tuple[float, float]] = {}
for t in t_eval:
    rnd = np.random.uniform(low=0, high=1, size=2)
    inputs[t] = (float(rnd[0]), float(rnd[1]))'''

np.random.seed(104)
random.seed(104)
sta: SymbolicTimedAutomaton = build_ode_sta()
sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "symbolic_timed_automata/lib/wordgen",
                                               length=SIGNAL_LENGTH)
samples = sta_input_gen.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, TOT_N_SIGNALS)

word = samples[0]
print(word)

t = 0
initial_u: tuple[float, float] = (0.7, 0.3)
word_dates: list[float] = [0]
word_values: list[tuple[float, float]] = [initial_u]

for step in word:
    t += step["delay"]
    word_dates += [t/10]
    word_values += [(step["vars"]["v1"], step["vars"]["v2"])]


inputs: dict[float, tuple[float, float]] = {0: initial_u}
for t in t_eval:
    previous_event_time_idx = max(0, bisect.bisect_left(word_dates, t)-1)
    event_time = word_dates[previous_event_time_idx]
    inputs[t] = word_values[previous_event_time_idx]

#sys.exit(0)






# Solve the ODE
sol = solve_ivp(build_system(gain=4, inputs=inputs), t_span, z0, t_eval=t_eval, method='LSODA')

# Calculate output y(t) = x1² + x2²
x1 = sol.y[0]  # Fixed index for x1
x2 = sol.y[1]  # Fixed index for x2
y = x1 ** 2 + x2 ** 2

for i, t in enumerate(t_eval):
    if t >= 1.0 and y[i] < 1e-6:
        print("Falsified!")
        break

# Create subplots
fig = make_subplots(rows=3, cols=1, subplot_titles=('State Variables', 'Input variables', 'Output y(t) (log scale)'))

v1_values = [v1 for v1, _ in word_values]
v2_values = [v2 for _, v2 in word_values]

# Add state variables to first subplot
fig.add_trace(go.Scatter(x=sol.t, y=x1, name='x₁(t)'), row=1, col=1)
fig.add_trace(go.Scatter(x=sol.t, y=x2, name='x₂(t)'), row=1, col=1)
fig.add_vline(x=1, line_dash="dash", line_color="red", row=1, col=1)
fig.add_trace(go.Scatter(x=sol.t, y=v1_values, name='v₁(t)'), row=2, col=1)
fig.add_trace(go.Scatter(x=sol.t, y=v2_values, name='v₂(t)'), row=2, col=1)

# Add output to second subplot
fig.add_trace(go.Scatter(x=sol.t, y=y, name='y(t)'), row=3, col=1)
fig.add_vline(x=1, line_dash="dash", line_color="red", row=3, col=1)

# Update layout
fig.update_layout(
    height=600,
    width=800,
    title_text="System Behavior Analysis",
    showlegend=True
)

# Set log scale for y-axis in second subplot
fig.update_yaxes(type="log", row=3, col=1)

# Add grid visibility settings
fig.update_xaxes(showgrid=True, row=1, col=1)
fig.update_yaxes(showgrid=True, row=1, col=1)
fig.update_xaxes(showgrid=True, row=2, col=1)
fig.update_yaxes(showgrid=True, row=2, col=1)

fig.show()


