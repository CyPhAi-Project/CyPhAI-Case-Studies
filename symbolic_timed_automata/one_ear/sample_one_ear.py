import math
import random
import time

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from symbolic_timed_automata.lib.syma.syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.one_ear.one_ear_sta import build_one_ear_sta

STA_OUT_FNAME = "sta/output/synthetic/one_ear/sta.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/synthetic/one_ear/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/synthetic/one_ear/concrete_trajectories.json"

SIGNAL_LENGTH = 5
TOT_N_SIGNALS = 10**6
N_WORDS_BATCH = 10**5
DEBUG = False


def sample_isotropic(length: int, n_signals:int):
    signals = []
    for i_signal in range(n_signals):
        signal = []

        current_time = 0.0
        last_reset_x = 0.0
        last_reset_y = 0.0

        for _ in range(length):
            x = current_time - last_reset_x
            y = current_time - last_reset_y

            d_max = min(1.0 - x, 1.0 - y)

            # Sample delay and update current time
            delay = np.random.uniform(0, d_max)
            current_time += delay

            # Choose action based on probabilities
            #action = np.random.choice(['a', 'b'], p=[1 / 6, 5 / 6])
            action = 'a'

            # Reset the corresponding clock
            if action == 'a':
                last_reset_y = current_time
                svars = sample_values_a()
            else:
                last_reset_x = current_time
                svars = sample_values_b()
            signal.append(dict(vars=svars, action=action, delay=delay))
        sig_list = [(st['delay'], st['vars'][0], st['vars'][1], st['action']) for st in signal]
        signals.append(sig_list)
    return signals


def quantize_3(value):
    return np.digitize(value, bins=[1 / 3, 2 / 3], right=False)

def quantize_4(value):
    return np.digitize(value, bins=[0.25, 0.5, 0.75], right=False)

def quantize_5(value):
    return np.digitize(value, bins=[0.2, 0.4, 0.6, 0.8], right=False)

def quantize_10(value):
    return np.digitize(value, bins=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], right=False)

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
        w = tuple(item
                  for sublist in (
                      [
                          quantize_10(step['delay']),
                          int(step['vars']['v1']),
                          int(step['vars']['v2']),
                      ] for step in sample)
                  for item in sublist)
        res.append(w)
    return res




def generate_signals_as_tuples_isotropic(length:int, n_signals:int) -> list[tuple]:
    res = []
    samples = sample_isotropic(length, n_signals)
    for i, sample in enumerate(samples):
        w = tuple(item
              for sublist in (
                  [
                      quantize_10(step[0]),
                      int(step[1]),
                      int(step[2]),
                  ] for step in sample)
              for item in sublist)
        res.append(w)
    return res



if __name__ == "__main__":


    '''plot_words_discovered_over_time(words_sta=words_sta, words_isotropic=words_isotropic)
    sys.exit(0)'''

    np.random.seed(104)
    random.seed(104)

    sta: SymbolicTimedAutomaton = build_one_ear_sta()

    sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "../lib/wordgen", length=SIGNAL_LENGTH)

    A_sta = set()
    sta_mean = 0
    A_isotropic = set()
    isotropic_mean = 0
    n_samples = 0
    history_sta = []
    history_isotropic = []

    sta_total_time = 0
    isotropic_total_time = 0

    beginning_time = time.time()
    n_batches = int(TOT_N_SIGNALS/N_WORDS_BATCH)
    for batch in range(n_batches):
        start_time = time.time()
        samples_sta = generate_signals_as_tuples_sta(sta_input_gen, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        sta_total_time += elapsed_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with STA in {elapsed_time:.3f} seconds")
        start_time = time.time()
        samples_isotropic = generate_signals_as_tuples_isotropic(SIGNAL_LENGTH, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        isotropic_total_time += elapsed_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with isotropic sampling in {elapsed_time:.3f} seconds")

        for w in samples_sta:
            A_sta.add(w)
        for w in samples_isotropic:
            A_isotropic.add(w)



        n_samples += N_WORDS_BATCH
        history_sta.append((n_samples, len(A_sta)))
        history_isotropic.append((n_samples, len(A_isotropic)))
        print(f"STA: Found {len(A_sta)} new words after {n_samples} samples")
        print(f"Isotropic: Found {len(A_isotropic)} new words after {n_samples} samples")

    total_elapsed_time = time.time() - beginning_time
    print(f"\tCompleted generating {TOT_N_SIGNALS} signals in {total_elapsed_time:.3f} seconds")
    print("words_sta =", history_sta)
    print("words_isotropic =", history_isotropic)


    print("Total generation time for STA: ", sta_total_time)
    print("Total generation time for Isotropic: ", isotropic_total_time)

    if A_sta == A_isotropic:
        print("Sampled the same words with the two methods!")

    A_intersection = A_sta.intersection(A_isotropic)
    print("Intersection size: ", len(A_intersection))


    history_array_sta = np.array(history_sta)
    # Save the array in compressed format
    np.savez_compressed(f"out/sampling/one_ear/sta/history{TOT_N_SIGNALS}_L{SIGNAL_LENGTH}_sta.npz",
                        array=history_array_sta)

    history_array_isotropic = np.array(history_isotropic)
    # Save the array in compressed format
    np.savez_compressed(f"out/sampling/one_ear/sta/history{TOT_N_SIGNALS}_L{SIGNAL_LENGTH}_isotropic.npz",
                        array=history_array_isotropic)



