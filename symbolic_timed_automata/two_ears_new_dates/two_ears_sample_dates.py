import random
import time
from collections import defaultdict

import numpy as np
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.generation.input_generator import InputGenerator

from symbolic_timed_automata.two_ears_new_dates.two_ears_sta_formats import build_two_ears_sta_formats

import plotly.io as pio
pio.kaleido.scope.mathjax = None
output_path = "symbolic_timed_automata/experiments/output/two_ears/sample_dates"


STA_OUT_FNAME = f"{output_path}/dates_sta.prism"
ABSTRACT_TRAJ_FNAME = f"{output_path}/dates_sta_abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = f"{output_path}/dates_sta_concrete_trajectories.json"

SIGNAL_LENGTH = 5
TOT_N_SIGNALS = 10**6
N_WORDS_BATCH = 10**4
DEBUG = False


def compute_word(sample) -> str:
    return "".join([s["action"] for s in sample])


def generate_signals_as_strings(generator, n_signals:int) -> list[str]:
    res = []
    samples = generator.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, n_signals)
    for sample in samples:
        word: str = compute_word(sample)
        res.append(word)
    return res


import plotly.graph_objects as go


def plot_probability_comparison(exact_probs, uniform_probs, x_labels):
    """
    Create a side-by-side bar chart comparing exact and uniform probabilities.

    Parameters:
    - exact_probs: List of 32 exact probabilities
    - uniform_probs: List of 32 uniform probabilities
    - x_labels: List of 32 strings for x-axis labels
    """
    # Create figure
    fig = go.Figure()

    # Add exact_probs bars
    fig.add_trace(go.Bar(
        x=x_labels,
        y=exact_probs,
        name='Exact Probabilities',
        marker_color='salmon',
        opacity=0.9,
        width=0.4  # Slightly narrower bars
    ))

    # Add uniform_probs bars
    fig.add_trace(go.Bar(
        x=x_labels,
        y=uniform_probs,
        name='Uniform Sampling Probabilities',
        marker_color='lightblue',
        opacity=0.9,
        width=0.4
    ))

    # Customize layout
    fig.update_layout(
        # title='Comparison of Exact vs Uniform Probabilities',
        # xaxis_title='Category',
        yaxis_title='Probability',
        font=dict(
            #family="Times New Roman, serif",
            size=12,
            color="black"
        ),
        barmode='group',  # This creates side-by-side bars
        margin=dict(l=50, r=50, b=150, t=50),
        width=1200,  # Wider to accommodate all labels
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        bargap=0.15,  # Gap between bars of different categories
        bargroupgap=0.1  # Gap between bars of the same category
    )

    # Rotate x-axis labels and adjust tick spacing
    fig.update_xaxes(
        tickangle=45,
        tickmode='array',
        tickvals=x_labels,
        ticktext=x_labels
    )

    return fig

if __name__ == "__main__":
    if True:
        np.random.seed(104)
        random.seed(104)
        run_start_time = time.time()

        sta: SymbolicTimedAutomaton = build_two_ears_sta_formats()


        sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "symbolic_timed_automata/lib/wordgen", length=SIGNAL_LENGTH)


        words = set()
        words_count_sta = defaultdict(lambda:0)
        n_batches = int(TOT_N_SIGNALS / N_WORDS_BATCH)
        for batch in range(n_batches):
            print(f"Discovered words after {batch*N_WORDS_BATCH} samples: {len(words_count_sta)}")
            words_str = generate_signals_as_strings(sta_input_gen, N_WORDS_BATCH)

            for w in words_str:
                words_count_sta[w] += 1

            words.update(set(words_str))


        print(f"Discovered words after {batch*TOT_N_SIGNALS} samples: {len(words_count_sta)}")
        print(f"Number of words: {len(words_count_sta)}")
        avg_samples_per_words = np.mean(list(words_count_sta.values()))
        print(f"Average number of samples per word: {avg_samples_per_words}")
        std_samples_per_words = np.std(list(words_count_sta.values()))
        print(f"Standard error of average of samples per word: {std_samples_per_words}")

        words_lst = list(words)
        words_lst.sort()

        uniform_probs = []
        for w in words_lst:
            print(f"Prob of word {w}: {words_count_sta[w]/TOT_N_SIGNALS}")
            uniform_probs.append(words_count_sta[w]/TOT_N_SIGNALS)


        print(uniform_probs)
        print(words_lst)
        run_elapsed_time = time.time() - run_start_time
        print(f"Total elapsed time: {run_elapsed_time}")
    else:


        uniform_probs = [4e-06, 0.000216, 0.000809, 0.002016, 0.001217, 0.01204, 0.006052, 0.010159, 0.000797, 0.012324, 0.024585, 0.06119,
         0.006232, 0.061268, 0.02024, 0.025372, 0.000199, 0.004046, 0.012359, 0.030517, 0.012384, 0.122496, 0.061087,
         0.101894, 0.00203, 0.030591, 0.061219, 0.153333, 0.01021, 0.102038, 0.025585, 0.025491]
        words_lst = ['aaaaa', 'aaaab', 'aaaba', 'aaabb', 'aabaa', 'aabab', 'aabba', 'aabbb', 'abaaa', 'abaab', 'ababa', 'ababb',
         'abbaa', 'abbab', 'abbba', 'abbbb', 'baaaa', 'baaab', 'baaba', 'baabb', 'babaa', 'babab', 'babba', 'babbb',
         'bbaaa', 'bbaab', 'bbaba', 'bbabb', 'bbbaa', 'bbbab', 'bbbba', 'bbbbb']

    exact_probs = [8.16153306237043757e-06, 0.000204038326559260943, 0.00081615330623704377,
                   0.00204038326559260932, 0.00122422995935556555, 0.0122422995935556559,
                   0.00612114979677782795, 0.0102019163279630457, 0.00081615330623704377,
                   0.0122422995935556559, 0.0244845991871113118, 0.0612114979677782778,
                   0.00612114979677782795, 0.0612114979677782778, 0.0204038326559260914,
                   0.0255047908199076169, 0.000204038326559260943, 0.00408076653118521863,
                   0.0122422995935556559, 0.0306057489838891389, 0.0122422995935556559,
                   0.122422995935556556, 0.0612114979677782778, 0.102019163279630468,
                   0.00204038326559260932, 0.0306057489838891389, 0.0612114979677782778,
                   0.153028744919445681, 0.0102019163279630457, 0.102019163279630468,
                   0.0255047908199076169, 0.0255047908199076169]
    print(len(exact_probs), len(uniform_probs))

    fig = plot_probability_comparison(exact_probs, uniform_probs, words_lst)
    fig.show()

    fig.write_image("sta_sampling_vs_exact.pdf", width=1000, height=350, scale=2)

    diff = []
    for i in range(32):
        diff.append(abs(exact_probs[i] - uniform_probs[i]))

    print(diff)
