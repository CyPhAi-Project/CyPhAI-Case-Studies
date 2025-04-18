import math
import random
import time

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.two_ears.two_ears_sta import build_two_ears_sta, CLOCK_UB

STA_OUT_FNAME = "symbolic_timed_automata/two_ears/output/sta.prism"
ABSTRACT_TRAJ_FNAME = "symbolic_timed_automata/two_ears/output/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "symbolic_timed_automata/two_ears/output/concrete_trajectories.json"

SIGNAL_LENGTH = 4
TOT_N_SIGNALS = 10**6
N_WORDS_BATCH = 10**4
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
            action = np.random.choice(['a', 'b'], p=[1 / 6, 5 / 6])


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

def truncate_decimal(number, digits):
    return math.floor(number * 10**digits) / 10**digits


def sample_isotropic_old(length: int, n_signals:int) -> list:
    signals = []
    for i_signal in range(n_signals):
        signal = []
        t = 0
        for i_step in range(length):
            action = 'a' if np.random.random() < 0.16666666666666666 else 'b'
            # = np.random.choice(actions)
            #action = actions_choices[i_signal][i_step]
            if action == 'a':
                vars = sample_values_a()
            else: # 'b':
                vars = sample_values_b()
            while True:
                # Compute delay so that the timing constraints are satisfied
                if len(signal) == 0 or signal[-1]['action'] != action:
                    delay = np.random.uniform(low=0, high=CLOCK_UB)
                    t = delay
                else:
                    delay = np.random.uniform(low=0, high=CLOCK_UB-t)
                    t += delay

                if len(signal) == 0 or signal[-1]['delay'] + delay < CLOCK_UB:
                    break

            signal.append(dict(vars=vars, action=action, delay=delay))
        sig_list = [ (st['delay'], st['vars'][0], st['vars'][1], st['action']) for st in signal]
        signals.append(sig_list)
    return signals

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
                          # step['delay'],
                          #truncate_decimal(step['delay'], 1),
                          #round(step['delay'], 1),
                          quantize_3(step['delay']),
                          # int(step['delay']),
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
                      #step[0],
                      # truncate_decimal(step[0], 1),
                      #round(step[0], 1),
                      quantize_3(step[0]),
                      #int(step[0]),
                      int(step[1]),
                      int(step[2]),
                  ] for step in sample)
              for item in sublist)
        res.append(w)
    return res



def consecutive_bs(A):
    # Function to count consecutive 'a's in a row
    def count_consecutive_b(word):
        count = 0
        max_count = 0
        cons_delay = 0
        for i, element in enumerate(word):
            if not element.isalpha():
                continue
            delay = float(word[i - 1])
            cons_delay += delay
            if element == 'b' and cons_delay < 0.1:
                count += 1
                if count > max_count:
                    max_count = count
            else:
                count = 0
                if element == 'b' and delay < 0.1:
                    cons_delay = delay
                else:
                    cons_delay = 0
        return max_count

    # Convert the set of tuples to a NumPy array
    array = np.array(list(A))
    # Apply the function to each row in the array
    consecutive_b_counts = np.apply_along_axis(count_consecutive_b, axis=1, arr=array)
    # Calculate the mean of the consecutive 'a' counts
    mean_consecutive_b = np.mean(consecutive_b_counts)
    std_consecutive_b = np.std(consecutive_b_counts)
    return mean_consecutive_b, std_consecutive_b
    # print("Mean number of consecutive 'b' for STA:", mean_consecutive_b, "+/-", np.std(consecutive_b_counts))

if __name__ == "__main__":


    np.random.seed(104)
    random.seed(104)

    sta: SymbolicTimedAutomaton = build_two_ears_sta()

    sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "../lib/wordgen", length=SIGNAL_LENGTH)
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
    '''start_time = time.time()

    samples_sta = generate_signals_as_tuples_sta(sta_input_gen, TOT_N_SIGNALS)
    elapsed_time = time.time() - start_time
    print(f"\tCompleted generating {N_WORDS_BATCH} signals with STA in {elapsed_time:.1f} seconds")'''

    history_mean_sta = []
    history_mean_isotropic = []

    beginning_time = time.time()
    n_batches = int(TOT_N_SIGNALS/N_WORDS_BATCH)
    for batch in range(n_batches):
        start_time = time.time()
        samples_sta = generate_signals_as_tuples_sta(sta_input_gen, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with STA in {elapsed_time:.3f} seconds")
        start_time = time.time()
        samples_isotropic = generate_signals_as_tuples_isotropic(SIGNAL_LENGTH, N_WORDS_BATCH)
        elapsed_time = time.time() - start_time
        print(f"\tCompleted generating {N_WORDS_BATCH} signals with isotropic sampling in {elapsed_time:.3f} seconds")



        #for w in samples_sta[batch*N_WORDS_BATCH:(batch+1)*N_WORDS_BATCH]:
        for w in samples_sta:
            A_sta.add(w)
        for w in samples_isotropic:
            A_isotropic.add(w)



        n_samples += N_WORDS_BATCH
        history_sta.append((n_samples, len(A_sta)))
        history_isotropic.append((n_samples, len(A_isotropic)))
        print(f"STA: Found {len(A_sta)} new words after {n_samples} samples")
        print(f"Isotropic: Found {len(A_isotropic)} new words after {n_samples} samples")
        #sta_mean, sta_std = consecutive_bs(A_sta_raw)

    total_elapsed_time = time.time() - beginning_time
    print(f"\tCompleted generating {TOT_N_SIGNALS} signals in {total_elapsed_time:.3f} seconds")
    print("words_sta =", history_sta)
    print("words_isotropic =", history_isotropic)



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



