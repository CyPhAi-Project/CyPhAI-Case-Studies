import math
import random
from collections import defaultdict

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.generation.input_generator import InputGenerator
from syma.volume.constraint_abstraction import ConstraintAbstraction

from symbolic_timed_automata.two_ears.sample_two_ears import sample_values_a, sample_values_b
from symbolic_timed_automata.two_ears.two_ears_sta import build_two_ears_sta

'''signals = sample_isotropic(length=2, n_signals=10000)

date_signals = []

for signal in signals:
    t = 0
    date_signal = []
    for step in signal:
        t += step[0]
        date_signal += [t]
    date_signals.append(date_signal)

dates_t1 = [ds[0] for ds in date_signals]
dates_t2 = [ds[1] for ds in date_signals]
dates_sum = [sum(ds) for ds in date_signals]
import plotly.express as px

fig = px.scatter(x=dates_t1, y=dates_t2, opacity=0.8, labels={'x':'t1', 'y':'t2'})
# Show the plot
fig.update_traces(marker=dict(size=1, line=dict(width=0.5, color='DarkSlateGrey')))
fig.show()
'''

def sample_isotropic(length: int, n_signals:int):
    signals = []
    for i_signal in range(n_signals):
        signal: list[dict[str, float|str|dict[str,float]]] = []

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
            signal.append(dict(vars=dict(v1=svars[0], v2=svars[1]), action=action, delay=delay))
        signals.append(signal)
    return signals


STA_OUT_FNAME = "symbolic_timed_automata/dates/output/dates_sta.prism"
ABSTRACT_TRAJ_FNAME = "symbolic_timed_automata/dates/output/dates_sta_abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "symbolic_timed_automata/dates/output/dates_sta_concrete_trajectories.json"

SIGNAL_LENGTH = 3
TOT_N_SIGNALS = 10**6
N_WORDS_BATCH = 10**5
DEBUG = False


def compute_word_hash(word, abstractions: list[ConstraintAbstraction]) -> tuple:
    int_dates = []
    frac_dates = []
    triangles: list[int] = []
    t = 0
    for step in word:
        delay = step['delay']
        t += delay

        fractional_part, integer_part = math.modf(t)

        int_dates.append(int(integer_part))
        frac_dates.append(fractional_part)
        point = dict(v1=step['vars']['v1'], v2=step['vars']['v2'])

        abs = [i for i in range(len(abstractions)) if abstractions[i].contains(point)]
        if len(abs) != 1:
            if len(abs) == 0:
                raise RuntimeError(f"Did not find a polyhedron containing the point ({point['v1']}, {point['v2']})")
            if len(abs) > 1:
                raise RuntimeError(f"More than one polyhedron contains the point ({point['v1']}, {point['v2']})")
        triangles.append(abs[0])

    perm = [int(x) for x in np.argsort(np.argsort(np.array(frac_dates))).tolist()]
    perm.extend(triangles)
    return tuple(perm)


def generate_signals_as_tuples_sta(generator, n_signals:int, abstractions: list[ConstraintAbstraction]) -> list[tuple]:
    res = []
    samples = generator.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, n_signals)
    for sample in samples:
        word_hash: tuple = compute_word_hash(sample, abstractions)
        res.append(word_hash)
    return res

def generate_signals_as_tuples_isotropic(n_signals:int, abstractions: list[ConstraintAbstraction]) -> list[tuple]:
    res = []
    samples = sample_isotropic(SIGNAL_LENGTH, n_signals)
    for sample in samples:
        word_hash: tuple = compute_word_hash(sample, abstractions)
        res.append(word_hash)
    return res


def plot_results(words_count: dict):
    hashes_list = list(words_count.keys())
    hashes_list.sort()

    bin_size = 1

    x = list(range(int(len(hashes_list)/bin_size)))


    y = [sum([words_count[hash] for hash in hashes_list[i:i + bin_size]]) for i in range(0, len(hashes_list), bin_size)]

    labels = [i for i in range(len(x))]
    import plotly.express as px
    import pandas as pd

    # Sample data
    data = {
        'word': x,  # Categories for the x-axis
        'samples': y,  # Values for the y-axis
        'CustomLabel': labels,
    }

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Create a bar chart using Plotly Express
    fig = px.bar(df, x='word', y='samples',
                 labels={'word': 'X-Axis', 'samples': 'Y-Axis'},
                 hover_data=['CustomLabel'])

    # Update layout for better visualization
    fig.update_layout(
        title="Bar Chart Example",
        xaxis_title="Words",
        yaxis_title="Samples",
        template="plotly_white"  # Use a clean template
    )

    # Show the plot
    fig.show()


if __name__ == "__main__":
    np.random.seed(104)
    random.seed(104)
    from constraints import abstractions

    '''sta: SymbolicTimedAutomaton = build_two_ears_sta()


    sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "symbolic_timed_automata/lib/wordgen", length=SIGNAL_LENGTH)


    #words = set()
    words_count_sta = defaultdict(lambda:0)
    n_batches = int(TOT_N_SIGNALS / N_WORDS_BATCH)
    for batch in range(n_batches):
        print(f"Discovered words after {batch*N_WORDS_BATCH} samples: {len(words_count_sta)}")
        hashes = generate_signals_as_tuples_sta(sta_input_gen, N_WORDS_BATCH, abstractions)

        for hash in hashes:
            words_count_sta[hash] += 1

        #words.update(set(hashes))

    print(f"Discovered words after {batch*TOT_N_SIGNALS} samples: {len(words_count_sta)}")
    print(f"Number of words: {len(words_count_sta)}")
    avg_samples_per_words = np.mean(list(words_count_sta.values()))
    print(f"Average number of samples per word: {avg_samples_per_words}")
    std_samples_per_words = np.std(list(words_count_sta.values()))
    print(f"Standard error of average of samples per word: {std_samples_per_words}")'''





    words_count_isotropic = defaultdict(lambda:0)
    n_batches = int(TOT_N_SIGNALS / N_WORDS_BATCH)
    for batch in range(n_batches):
        print(f"Discovered words after {batch * N_WORDS_BATCH} samples: {len(words_count_isotropic)}")
        words_hashes_isotropic = generate_signals_as_tuples_isotropic(n_signals=N_WORDS_BATCH,abstractions=abstractions)
        for hash in words_hashes_isotropic:
            words_count_isotropic[hash] += 1



    plot_results(words_count_isotropic)

