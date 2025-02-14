import math
import random
import time

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.tunnel.tunnel_sta import build_tunnel_sta

STA_OUT_FNAME = "sta/output/synthetic/output/sta.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/synthetic/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/synthetic/output/concrete_trajectories.json"

SIGNAL_LENGTH = 20
TOT_N_SIGNALS = 10**4
N_WORDS_BATCH = 10**3
DEBUG = False


def sample_isotropic(length: int, n_signals:int):
    signals = []
    signals_with_clocks = []
    for i_signal in range(n_signals):
        signal = []
        signal_with_clocks = []
        current_time = 0.0
        last_reset_x = 0.0
        last_reset_y = 0.0

        for _ in range(length):
            x = current_time - last_reset_x
            y = current_time - last_reset_y

            if 6 <= x <= 9:
                # Choose action based on probabilities
                action = np.random.choice(['a', 'b'], p=[5/6, 1/6])
            else:
                action = 'a'

            if action == 'a':
                d_min = 0
                d_max = min(10.0 - x, 3.0 - y)
            else: #action == 'b'
                d_min = max(8-x, 1)
                d_max = min(10-x, 2)

            # Sample delay and update current time
            delay = np.random.uniform(d_min, d_max)
            current_time += delay

            # Reset the corresponding clock
            if action == 'a':
                last_reset_y = current_time
                svars = sample_values_a()
            else:
                last_reset_x = current_time
                svars = sample_values_b()
            signal.append(dict(vars=svars, action=action, delay=delay))
            signal_with_clocks.append(dict(vars=svars, action=action, delay=delay, x=x+delay, y=y+delay))
        sig_list = [(st['delay'], st['vars'][0], st['vars'][1], st['action']) for st in signal]
        signals.append(sig_list)
        signals_with_clocks.append(signal_with_clocks)
    return signals, signals_with_clocks


def quantize_3(value):
    return np.digitize(value, bins=[1 / 3, 2 / 3], right=False)

def quantize_4(value):
    return np.digitize(value, bins=[0.25, 0.5, 0.75], right=False)

def truncate_decimal(number, digits):
    return math.floor(number * 10**digits) / 10**digits


def sample_values_a():
    while True:
        v = np.random.uniform(low=0, high=2, size=2)
        if v[0] == 2 or v[1] == 2:
            raise ValueError()
        if v[0] + v[1] <= 1:
            return v


def sample_values_b():
    while True:
        v = np.random.uniform(low=0, high=2, size=2)
        if v[0] == 2 or v[1] == 2:
            raise ValueError()
        if 2*v[0] + v[1] >= 2 and v[0] + v[1] <= 3:

            return v


def generate_signals_as_tuples_sta(generator, n_signals:int) -> list[tuple]:
    res = []
    samples = generator.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, n_signals)
    for sample in samples:
        # w = tuple( truncate_decimal(item, 1)
        w = tuple(item
                  for sublist in (
                      [
                          int(step['delay']),
                          int(step['vars']['v1']),
                          int(step['vars']['v2']),
                      ] for step in sample)
                  for item in sublist)
        res.append(w)
    return res




def generate_signals_as_tuples_isotropic(length:int, n_signals:int):
    res = []
    clock_values_x = []
    clock_values_y = []
    samples, samples_with_clocks = sample_isotropic(length, n_signals)
    for i, sample in enumerate(samples):
        w = tuple(item
              for sublist in (
                  [
                      int(step[0]),
                      int(step[1]),
                      int(step[2]),
                  ] for step in sample)
              for item in sublist)
        res.append(w)
        for step in samples_with_clocks[i]:
            clock_values_x.append(step["x"])
            clock_values_y.append(step["y"])


    return res, clock_values_x, clock_values_y



if __name__ == "__main__":
    np.random.seed(104)
    random.seed(104)

    sta: SymbolicTimedAutomaton = build_tunnel_sta()

    sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "sta/lib/wordgen", length=SIGNAL_LENGTH)
    generation_method = "isotropic"

    A_sta = set()
    #A_sta_raw = []
    sta_mean = 0
    A_isotropic = set()
    #A_isotropic_raw = []
    isotropic_mean = 0
    n_samples = 0
    history_sta = []
    history_isotropic = []


    history_mean_sta = []
    history_mean_isotropic = []

    beginning_time = time.time()
    n_batches = int(TOT_N_SIGNALS/N_WORDS_BATCH)
    clock_values_x = []
    clock_values_y = []
    for batch in range(n_batches):
        start_time = time.time()
        samples_sta = generate_signals_as_tuples_sta(sta_input_gen, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with STA in {elapsed_time:.3f} seconds")
        start_time = time.time()
        samples_isotropic, clock_values_samples_x, clock_values_samples_y = generate_signals_as_tuples_isotropic(SIGNAL_LENGTH, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with isotropic sampling in {elapsed_time:.3f} seconds")

        for w in samples_sta:
            A_sta.add(w)
        for w in samples_isotropic:
            A_isotropic.add(w)

        clock_values_x.extend(clock_values_samples_x)
        clock_values_y.extend(clock_values_samples_y)



        n_samples += N_WORDS_BATCH
        history_sta.append((n_samples, len(A_sta)))
        history_isotropic.append((n_samples, len(A_isotropic)))
        print(f"STA: Found {len(A_sta)} new words after {n_samples} samples")
        print(f"Isotropic: Found {len(A_isotropic)} new words after {n_samples} samples")

    total_elapsed_time = time.time() - beginning_time
    print(f"\tCompleted generating {TOT_N_SIGNALS} signals in {total_elapsed_time:.3f} seconds")
    print("words_sta =", history_sta)
    print("words_isotropic =", history_isotropic)

    # x and y given as array_like objects
    import plotly.express as px

    fig = px.scatter(x=clock_values_x, y=clock_values_y, opacity=0.5)
    # Show the plot
    fig.update_traces(marker=dict(size=1, line=dict(width=0.5, color='DarkSlateGrey')))
    fig.show()



    if A_sta == A_isotropic:
        print("Sampled the same words with the two methods!")

    A_intersection = A_sta.intersection(A_isotropic)
    print("Intersection size: ", len(A_intersection))


    history_array_sta = np.array(history_sta)
    # Save the array in compressed format
    np.savez_compressed(f"out/sampling/two_ears/sta/history{TOT_N_SIGNALS}_L{SIGNAL_LENGTH}_sta.npz",
                        array=history_array_sta)

    history_array_isotropic = np.array(history_isotropic)
    # Save the array in compressed format
    np.savez_compressed(f"out/sampling/two_ears/sta/history{TOT_N_SIGNALS}_L{SIGNAL_LENGTH}_isotropic.npz",
                        array=history_array_isotropic)



