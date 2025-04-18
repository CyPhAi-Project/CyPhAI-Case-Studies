import math
import random
from collections import defaultdict

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from symbolic_timed_automata.lib.syma.syma.generation.input_generator import InputGenerator
from symbolic_timed_automata.simglucose.cli import get_command_line_arguments
from symbolic_timed_automata.simglucose.params import get_meal_space
from symbolic_timed_automata.simglucose.penalties import breakfast_size
from symbolic_timed_automata.simglucose.sta.build_automaton_six_meals import build_sa_three_snacks
from symbolic_timed_automata.simglucose.sta.build_simglucose_sta import build_simglucose_sta
from symbolic_timed_automata.simglucose.utils import simglucose_isotropic_sampling

STA_OUT_FNAME = "symbolic_timed_automata/simglucose/histograms/output/sta_simglucose.prism"
ABSTRACT_TRAJ_FNAME = "symbolic_timed_automata/simglucose/histograms/output/sta_abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "symbolic_timed_automata/simglucose/histograms/output/sta_concrete_trajectories.json"





def compute_word_hash(word) -> tuple:
    int_dates = []
    frac_dates = []
    m_values: list[int] = []
    date = 0
    for step in word:
        delay = step['delay']
        date = date + delay
        if date > 24:
            break

        fractional_part, integer_part = math.modf(date)

        int_dates.append(int(integer_part))
        frac_dates.append(fractional_part)

        m_value: int = int(step['vars']['m']) #*10)
        m_values.append(m_value)

    perm = [int(x) for x in np.argsort(np.argsort(np.array(frac_dates))).tolist()]
    perm.extend(m_values)
    perm.extend(int_dates)
    return tuple(perm)

def generate_signals_as_tuples_isotropic(n_signals:int, dist_factor: float) -> list[tuple]:
    res = []
    samples = simglucose_isotropic_sampling(n_signals, dist_factor)
    for sample in samples:
        word_hash: tuple = compute_word_hash(sample)
        res.append(word_hash)
    return res

def generate_signals_as_tuples_sta(generator, n_signals:int) -> list[tuple]:
    res = []
    samples = generator.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, n_signals)
    for sample in samples:
        word_hash: tuple = compute_word_hash(sample)
        res.append(word_hash)
    return res

def plot_results_line(words_count: dict):
    hashes_list = list(words_count.keys())
    hashes_list.sort()

    # for 10**5, one of 1, 2, 3, 6, 59, 118, 177, 354, 277, 554, 831, 1.662, 16.343, 32.686, 49.029, 98.058.
    # for 10**6, one of 1, 2, 4, 8, 73, 146, 292, 584, 1543
    # bin_size = 25

    labels = [i for i in range(len(hashes_list))]
    x = labels
    #x = list(range(int(len(hashes_list) / bin_size)))

    #y = [sum([words_count[hash] for hash in hashes_list[i:i + bin_size]]) for i in range(0, len(hashes_list), bin_size)]
    y = [words_count[hash] for hash in hashes_list]

    import plotly.express as px
    import pandas as pd

    # Sample data
    # Sample data
    data = {
        'Alphabet': x,  # Categories for the x-axis
        'Samples': y,  # Values for the y-axis
        'CustomLabel': labels,
    }

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Plot
    fig = px.line(df, x="Alphabet", y="Samples", title="Test histogram", hover_data=['CustomLabel'])
    # Update layout for better visualization
    fig.update_layout(
        title="Bar Chart",
        # xaxis_title=f"Words (x {bin_size})",
        yaxis_title="Samples",
        template="plotly_white"  # Use a clean template
    )

    # Show the plot
    fig.show()


def plot_results(words_count: dict, bin_size: int=1):
    hashes_list = list(words_count.keys())
    hashes_list.sort()

    # for 10**5, one of 1, 2, 3, 6, 59, 118, 177, 354, 277, 554, 831, 1.662, 16.343, 32.686, 49.029, 98.058.
    # for 10**6, one of 1, 2, 4, 8, 73, 146, 292, 584, 1543
    #bin_size = 25

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
        title="Bar Chart",
        #xaxis_title=f"Words (x {bin_size})",
        yaxis_title="Samples",
        template="plotly_white"  # Use a clean template
    )

    # Show the plot
    fig.show()

def build_words_count(method: str, n_signals, n_batch, dist_factor, max_generated_hashes=2000, generator=None) -> dict:
    words_count = defaultdict(lambda: 0)
    n_batches = int(n_signals / n_batch)
    breaking = False
    tot_n_hashes = 0
    for batch in range(n_batches):
        print(f"Discovered words after {batch * n_batch} samples: {len(words_count)}")
        if breaking:
            break
        match method:
            case 'isotropic':
                words_hashes = generate_signals_as_tuples_isotropic(n_signals=n_batch, dist_factor=dist_factor)
            case 'sta':
                words_hashes = generate_signals_as_tuples_sta(generator=sta_input_gen, n_signals=n_batch)
            case _:
                raise ValueError(f"Unknown method: {method}")
        tot_n_hashes += len(words_hashes)


        for hash in words_hashes:
            if len(words_count) < max_generated_hashes:
                words_count[hash] += 1
            else:
                breaking = True
                break
    print(f"{method} generated {tot_n_hashes} word hashes")
    print(f"Discovered words after {batch * N_WORDS_BATCH} samples: {len(words_count)}")

    str_dict = dict()
    for k, v in words_count.items():
        str_dict[(str(k))] = v
    import json
    with open(f"symbolic_timed_automata/simglucose/histograms/output/dump_words_count_{method}.json", "w+") as file:
        json.dump(str_dict, file)

    return words_count



if __name__ == "__main__":
    args = get_command_line_arguments()

    np.random.seed(args.master_seed)
    random.seed(args.master_seed)


    if args.output is not None:
        output_path = args.output
    else:
        output_path = "/output/simglucose_sta"

    #sta = build_sa_three_snacks(dist_factor=args.dist_factor)

    SIGNAL_LENGTH = 7
    TOT_N_SIGNALS = 1*10**6
    N_WORDS_BATCH = 1*10**4
    DEBUG = False


    #sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "symbolic_timed_automata/lib/wordgen", length=SIGNAL_LENGTH)
    do_isotropic = True
    if do_isotropic:
        words_count_isotropic = build_words_count('isotropic',TOT_N_SIGNALS, N_WORDS_BATCH,
                                                  dist_factor=args.dist_factor, max_generated_hashes=100000)
        # plot_results(words_count_isotropic, bin_size=1)
        plot_results_line(words_count_isotropic)



    do_sta = True

    if do_sta:
        # STA
        np.random.seed(104)
        random.seed(104)

        sta: SymbolicTimedAutomaton = build_simglucose_sta(dist_factor=0.1)

        sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "/home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/lib/wordgen", length=SIGNAL_LENGTH)
        words_count_sta = build_words_count('sta', TOT_N_SIGNALS, N_WORDS_BATCH,args.dist_factor,
                                            max_generated_hashes=100000, generator=sta_input_gen)

        # plot_results(words_count_sta, bin_size=10)
        plot_results_line(words_count_sta)


