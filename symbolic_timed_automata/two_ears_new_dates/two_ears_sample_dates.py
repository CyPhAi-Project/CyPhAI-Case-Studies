import random
import time
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.generation.input_generator import InputGenerator

from symbolic_timed_automata.two_ears.sample_two_ears import sample_values_a, sample_values_b
from symbolic_timed_automata.two_ears_new_dates.two_ears_sta_formats import build_two_ears_sta_formats

import plotly.io as pio
pio.kaleido.scope.mathjax = None
output_path = "symbolic_timed_automata/experiments/output/two_ears/sample_dates"


STA_OUT_FNAME = f"{output_path}/dates_sta.prism"
ABSTRACT_TRAJ_FNAME = f"{output_path}/dates_sta_abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = f"{output_path}/dates_sta_concrete_trajectories.json"

SIGNAL_LENGTH = 5
TOT_N_SIGNALS = 1*10**6
N_WORDS_BATCH = 10**4
DEBUG = False

def sample_isotropic(n_signals:int):
    signals = []
    for i_signal in range(n_signals):
        signal = []

        current_time = 0.0
        last_reset_x = 0.0
        last_reset_y = 0.0

        for _ in range(SIGNAL_LENGTH):
            x = current_time - last_reset_x
            y = current_time - last_reset_y
            action = np.random.choice(['a', 'b'], p=[1 / 6, 5 / 6])
            if action == 'a':
                d_max = 1.0 - x
            else:
                d_max = 1.0 - y


            # Sample delay and update current time
            delay = np.random.uniform(0, d_max)
            current_time += delay

            # Choose action based on probabilities



            # Reset the corresponding clock
            if action == 'a':
                last_reset_y = current_time
                svars = sample_values_a()
            else:
                last_reset_x = current_time
                svars = sample_values_b()
            signal.append(dict(vars=dict(v1=svars[0], v2=svars[1]), action=action, delay=delay))
        #sig_list = [(st['delay'], st['vars'][0], st['vars'][1], st['action']) for st in signal]
        signals.append(signal)
    return signals

def compute_word(sample) -> str:
    return "".join([s["action"] for s in sample])


def generate_signals_as_strings(n_signals:int, generator: InputGenerator=None) -> list[tuple[str, Any]]:
    res = []
    if generator:
        samples = generator.generate_uniform(ABSTRACT_TRAJ_FNAME, CONCRETE_TRAJ_FNAME, n_signals)
    else:
        samples = sample_isotropic(n_signals)
    for sample in samples:
        word: str = compute_word(sample)
        res.append((word, sample))
    return res


import plotly.graph_objects as go


def plot_probability_comparison(exact_probs, uniform_probs, isotropic_probs, x_labels):
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
        name='Exact Uniform Probabilities',
        marker_color='salmon',
        opacity=0.9,
        width=0.3  # Slightly narrower bars
    ))

    # Add uniform_probs bars
    fig.add_trace(go.Bar(
        x=x_labels,
        y=uniform_probs,
        name='Empirical Uniform Probabilities',
        marker_color='lightblue',
        opacity=0.9,
        width=0.3
    ))

    # Add isotropic_probs bars
    fig.add_trace(go.Bar(
        x=x_labels,
        y=isotropic_probs,
        name='Empirical Isotropic Probabilities',
        marker_color='#93C572',#B2C9AB',  # Sage green
        opacity=0.9,
        width=0.3
    ))

    # Customize layout
    fig.update_layout(
        # title='Comparison of Exact vs Uniform Probabilities',
        # xaxis_title='Category',
        yaxis_type="log",  # Key change!
        yaxis_title='Probability (log scale)',
        # Adjust range to avoid empty space (optional)
        yaxis=dict(
            # range=[np.log10(0.01), np.log10(0.5)],  # Customize based on your data
            range=[np.log10(0.0006), np.log10(0.9)],  # Customize based on your data
            tickvals=[0.001, 0.01, 0.05, 0.1, 0.2, 0.4],  # Manual tick marks
            ticktext=["0.001", "0.01", "0.05", "0.1", "0.2", "0.4"]  # Human-readable labels
        ),

        #yaxis_title='Probability',
        font=dict(
            #family="Times New Roman, serif",
            size=12,
            color="black"
        ),
        barmode='group',  # This creates side-by-side bars
        margin=dict(l=50, r=50, b=50, t=50),
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

import plotly.express as px

def plot_ecdf_comparison(sta_samples, isotropic_samples, a=0, b=1, title="ECDF Comparison of Uniform vs. STA Sampling"):
    # Generate uniform and non-uniform (Gaussian) samples
    num_samples = len(sta_samples)
    mean = (a + b) / 2
    std_dev = (b - a) / 6
    uniform_samples = np.random.uniform(a, b, num_samples)

    # Combine into a tidy DataFrame for Plotly Express
    df = pd.DataFrame({
        "Value": np.concatenate([uniform_samples, sta_samples]),
        "Method": ["Uniform"] * num_samples + ["STA"] * num_samples
    })

    # Create ECDF plot
    fig = px.ecdf(
        df,
        x="Value",
        color="Method",
        title=title,
        labels={"Value": "Value", "ecdf": "Proportion ≤ x"},
    )
    fig.update_layout(legend_title_text="Sampling Method")
    fig.show()




def plot_xy_pairs(
        series1: list[tuple[float, float]],series2: list[tuple[float, float]],
        series1_name: str = "Series 1",
        series2_name: str = "Series 2",
        title: str = "Plot of XY Pairs",
        xaxis_title: str = "X",
        yaxis_title: str = "Y",
        opacity: float = 0.6,  # Transparency level (0=invisible, 1=opaque)
        a:float=0, b:float=1
):
    """
    Plots two series of (x, y) pairs as transparent dots (no lines).

    Args:
        series1: List of (x, y) tuples for the first series.
        series2: List of (x, y) tuples for the second series.
        series1_name: Legend name for Series 1.
        series2_name: Legend name for Series 2.
        title: Plot title.
        xaxis_title: X-axis label.
        yaxis_title: Y-axis label.
        opacity: Transparency of markers (0 to 1).
    """
    # Unzip the (x, y) pairs into separate lists
    x1, y1 = zip(*series1) if series1 else ([], [])
    x2, y2 = zip(*series2) if series2 else ([], [])

    fig = go.Figure()

    # Add Series 1 (dots only, transparent)
    fig.add_trace(
        go.Scatter(
            x=x1,
            y=y1,
            mode="markers",  # No lines, only markers
            name=series1_name,
            marker=dict(
                color="rgba(70, 130, 180, {})".format(opacity),  # Semi-transparent blue
                size=8,
                line=dict(width=0)  # No border around markers
            ),
        )
    )

    # Add Series 2 (dots only, transparent)
    fig.add_trace(
        go.Scatter(
            x=x2,
            y=y2,
            mode="markers",  # No lines, only markers
            name=series2_name,
            marker=dict(
                color="rgba(220, 60, 60, {})".format(opacity),  # Semi-transparent red
                size=8,
                line=dict(width=0)  # No border around markers
            ),
        )
    )

    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        xaxis=dict(range=[a, b]),  # Force X-axis to [a, b]
        yaxis=dict(range=[a, b]),  # Force Y-axis to [a, b]
        legend_title="Series",
    )

    fig.show()


from itertools import groupby


def sort_words(strings, custom_sort=False):
    if custom_sort:
        def custom_key(s):
            # 1. Number of consecutive 'b's (max length of 'b' groups)
            #consecutive_bs = max([len(list(g)) for k, g in groupby(s) if k == 'b'], default=0)

            # 2. Total number of 'b's
            total_bs = s.count('b')

            # 3. Reverse alphabetical order (higher priority for 'b's)
            reverse_alpha = -sum(ord(c) for c in s)  # 'b' > 'a' in ASCII

            #return (-consecutive_bs, -total_bs, reverse_alpha)
            return (-total_bs, reverse_alpha)

        return sorted(strings, key=custom_key)
    else:
        return sorted(strings)


def gen_word_counts_and_bbabb(method="STA",
                              generator:InputGenerator = None) -> dict[str, float]:
    generation_start_time = time.time()
    untimed_words: set[str] = set()
    words_count_sta = defaultdict(lambda: 0)
    n_batches = int(TOT_N_SIGNALS / N_WORDS_BATCH)
    bbabb_words_sta: list[Any] = []
    print(f"Generating {n_batches} batches of {TOT_N_SIGNALS} signals with {method} method")
    for batch in range(n_batches):
        print(f"Discovered words after {batch * N_WORDS_BATCH} samples: {len(words_count_sta)}")

        # superfluous if, just for clarity
        if method == "STA":
            gen_words: list[tuple[str, Any]] = generate_signals_as_strings(N_WORDS_BATCH, generator=generator)
        else:
            gen_words: list[tuple[str, Any]] = generate_signals_as_strings(N_WORDS_BATCH)

        for word, trace in gen_words:
            words_count_sta[word] += 1
            if word == "bbabb":
                bbabb_words_sta.append(trace)

        words_str = set([gw[0] for gw in gen_words])
        untimed_words.update(words_str)

    print(f"Total number of unique words discovered: {len(words_count_sta)}")

    '''# Sort the untimed words in alphabetical order
    untimed_words_lst: list[str] = list(untimed_words)
    # untimed_words_lst.sort()
    untimed_words_lst = sort_words(untimed_words_lst)'''


    empirical_sampling_probs: dict[str, float] = dict()
    for w in untimed_words: #untimed_words_lst:
        # print(f"Prob of word {w}: {words_count_sta[w] / TOT_N_SIGNALS}")
        empirical_sampling_probs[w] = (words_count_sta[w] / TOT_N_SIGNALS)

    print(empirical_sampling_probs)
    #print(untimed_words_lst)
    run_elapsed_time = time.time() - generation_start_time
    print(f"Total elapsed time for {method}: {run_elapsed_time}")

    '''sta_t12_samples: list[tuple[float, float]] = []
    sta_t3_samples: list[float] = []
    sta_t45_samples: list[tuple[float, float]] = []

    for w in bbabb_words_sta:
        sta_t12_samples.append((w[0]["delay"], w[1]["delay"]))
        sta_t3_samples.append(w[2]["delay"])
        sta_t45_samples.append((w[3]["delay"], w[4]["delay"]))'''


    # times
    #plot_xy_pairs(sta_t12_samples, None, series1_name="STA", series2_name="UNIFORM", title="t1 vs t2 - STA sampling")
    #plot_ecdf_comparison(sta_t3_samples, None, title="ECDF comparison for t3 with STA sampling")
    #plot_xy_pairs(sta_t45_samples, None, series1_name="STA", series2_name="UNIFORM", title="t4 vs t5 - STA sampling")

    # values

    for i in range(5):
        sta_v12_ti_samples: list[tuple[float, float]] = []
        for w in bbabb_words_sta:
            sta_v12_ti_samples.append((w[i]["vars"]["v1"], w[i]["vars"]["v2"]))
        #plot_xy_pairs(sta_v12_ti_samples, None, series1_name="STA", series2_name="UNIFORM",
        #              title=f"v1(t{i + 1}) vs v2(t{i + 1}) - STA sampling", a=0, b=2)

    return empirical_sampling_probs


if __name__ == "__main__":
    CUSTOM_SORT = True
    np.random.seed(104)
    random.seed(104)
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

    words_lst = ['aaaaa', 'aaaab', 'aaaba', 'aaabb', 'aabaa', 'aabab', 'aabba', 'aabbb', 'abaaa', 'abaab', 'ababa',
                 'ababb',
                 'abbaa', 'abbab', 'abbba', 'abbbb', 'baaaa', 'baaab', 'baaba', 'baabb', 'babaa', 'babab', 'babba',
                 'babbb',
                 'bbaaa', 'bbaab', 'bbaba', 'bbabb', 'bbbaa', 'bbbab', 'bbbba', 'bbbbb']

    # superfluous
    words_lst.sort()

    exact_probs_dict = {w: exact_probs[i] for i, w in enumerate(words_lst)}

    words_lst = sort_words(words_lst, custom_sort=CUSTOM_SORT)

    sorted_exact_probs = [exact_probs_dict[words_lst[i]] for i in range(len(words_lst))]

    if False:
        np.random.seed(104)
        random.seed(104)


        sta: SymbolicTimedAutomaton = build_two_ears_sta_formats()


        sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "symbolic_timed_automata/lib/wordgen", length=SIGNAL_LENGTH)

        empirical_sta_probs_dict: dict[str, float] = gen_word_counts_and_bbabb(method="STA", generator=sta_input_gen)
        empirical_isotropic_probs_dict: dict[str, float] = gen_word_counts_and_bbabb(method="Isotropic")



    else:


        #uniform_probs = [4e-06, 0.000216, 0.000809, 0.002016, 0.001217, 0.01204, 0.006052, 0.010159, 0.000797, 0.012324, 0.024585, 0.06119,
         #0.006232, 0.061268, 0.02024, 0.025372, 0.000199, 0.004046, 0.012359, 0.030517, 0.012384, 0.122496, 0.061087,
         #0.101894, 0.00203, 0.030591, 0.061219, 0.153333, 0.01021, 0.102038, 0.025585, 0.025491]


        #only alphabetical
        #empirical_sta_probs = [3e-06, 0.0002, 0.000849, 0.00213, 0.001164, 0.012273, 0.006093, 0.010158, 0.000803, 0.01229, 0.024561, 0.061155, 0.006126, 0.061052, 0.020357, 0.02531, 0.000178, 0.004086, 0.012196, 0.030409, 0.012541, 0.122395, 0.060897, 0.101916, 0.002063, 0.030441, 0.061481, 0.1532, 0.010355, 0.102086, 0.025458, 0.025774]
        #empirical_isotropic_probs = [0.00012, 0.00064, 0.000661, 0.003219, 0.000636, 0.003186, 0.003265, 0.015978, 0.000631, 0.003147, 0.003283, 0.015917, 0.00318, 0.016165, 0.01595, 0.08002, 0.000646, 0.003172, 0.003239, 0.016024, 0.003213, 0.015923, 0.016152, 0.080694, 0.003261, 0.015919, 0.016151, 0.080412, 0.016221, 0.080094, 0.080489, 0.402392]

        # custom sorting
        empirical_sta_probs_dict = {'abaab': 0.012279, 'bbaba': 0.061266, 'bbabb': 0.152761, 'bbbab': 0.101772, 'baabb': 0.030288, 'aaaaa': 8e-06, 'aaaba': 0.000729, 'bbbaa': 0.010145, 'aaabb': 0.002093, 'baaab': 0.004057, 'babbb': 0.101894, 'babab': 0.122185, 'aabab': 0.012186, 'aaaab': 0.000224, 'aabba': 0.006188, 'aabbb': 0.010054, 'abaaa': 0.000831, 'bbaaa': 0.002056, 'bbaab': 0.030763, 'ababa': 0.024651, 'bbbbb': 0.025617, 'abbab': 0.06132, 'abbba': 0.020363, 'abbbb': 0.025629, 'baaaa': 0.000209, 'aabaa': 0.001227, 'abbaa': 0.006061, 'babaa': 0.012354, 'baaba': 0.012314, 'bbbba': 0.025681, 'babba': 0.061024, 'ababb': 0.061771}
        empirical_isotropic_probs_dict = {'bbaba': 0.016151, 'abaab': 0.003147, 'bbabb': 0.080412, 'bbbab': 0.080094, 'baabb': 0.016024, 'aaaaa': 0.00012, 'aaaba': 0.000661, 'bbbaa': 0.016221, 'aaabb': 0.003219, 'baaab': 0.003172, 'babbb': 0.080694, 'babab': 0.015923, 'aabab': 0.003186, 'aaaab': 0.00064, 'aabba': 0.003265, 'aabbb': 0.015978, 'abaaa': 0.000631, 'bbaaa': 0.003261, 'bbaab': 0.015919, 'ababa': 0.003283, 'bbbbb': 0.402392, 'abbab': 0.016165, 'abbba': 0.01595, 'abbbb': 0.08002, 'baaaa': 0.000646, 'aabaa': 0.000636, 'abbaa': 0.00318, 'babaa': 0.003213, 'baaba': 0.003239, 'bbbba': 0.080489, 'babba': 0.016152, 'ababb': 0.015917}

    empirical_sta_probs: list[float] = [empirical_sta_probs_dict[words_lst[i]] for i in range(len(words_lst))]
    empirical_isotropic_probs: list[float] = [empirical_isotropic_probs_dict[words_lst[i]] for i in
                                              range(len(words_lst))]

    diff = []
    for i in range(32):
        diff.append(abs(sorted_exact_probs[i] - empirical_sta_probs[i]))

    print(diff)
    fig = plot_probability_comparison(sorted_exact_probs, empirical_sta_probs, empirical_isotropic_probs, words_lst)

    fig.show()
    fig.write_image("sta_sampling_vs_exact.pdf", width=1000, height=350, scale=2)