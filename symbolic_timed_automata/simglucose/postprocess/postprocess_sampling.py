import json
import scipy.stats as st
import plotly.io as pio

pio.kaleido.scope.mathjax = None

path = "/home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification"

with open(f"{path}/uniform_sta/dump.json", "r") as f:
    res_sta = json.load(f)

robustness_sta = []
for run in res_sta["runs"]:
    robustness_sta.extend(run["evaluations"])
#robustness_sta = res_sta['evaluations']

with open(f"{path}/isotropic/dump.json", "r") as f:
    res_isotropic = json.load(f)

robustness_isotropic = []
for run in res_isotropic["runs"]:
    robustness_isotropic.extend(run["evaluations"])

import numpy as np
import plotly.graph_objects as go

# Compute mean and standard deviation for both lists
mean_sta = np.mean(robustness_sta)
std_sta = np.std(robustness_sta)

mean_iso = np.mean(robustness_isotropic)
std_iso = np.std(robustness_isotropic)

# Generate normal distribution for both lists
x_sta = np.linspace(min(robustness_sta) - 1, max(robustness_sta) + 1, 500)
y_sta = (1 / (std_sta * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_sta - mean_sta) / std_sta) ** 2)

x_iso = np.linspace(min(robustness_isotropic) - 1, max(robustness_isotropic) + 1, 500)
y_iso = (1 / (std_iso * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_iso - mean_iso) / std_iso) ** 2)

# Bin data
# bins = 50
w = 2
bins = [-22 + w*k for k in range(50)]

bins_sta = np.histogram_bin_edges(robustness_sta, bins=bins)
bins_iso = np.histogram_bin_edges(robustness_isotropic, bins=bins)

hist_sta, bin_edges_sta = np.histogram(robustness_sta, bins=bins_sta, density=True)
hist_iso, bin_edges_iso = np.histogram(robustness_isotropic, bins=bins_iso, density=True)

# Create the histogram and normal distribution plots
fig = go.Figure()

# Bar for robustness_sta
fig.add_trace(go.Bar(
    x=(bin_edges_sta[:-1] + bin_edges_sta[1:]) / 2,
    y=hist_sta,
    name='STA',
    opacity=0.7,
    marker=dict(color='lightblue')
))

# Normal distribution for robustness_sta
'''fig.add_trace(go.Scatter(
    x=x_sta,
    y=y_sta,
    mode='lines',
    name=f"Normal (STA)<br>µ={mean_sta:.2f}, σ={std_sta:.2f}",
    line=dict(color='blue', dash='dash')
))'''

# Bar for robustness_iso
fig.add_trace(go.Bar(
    x=(bin_edges_iso[:-1] + bin_edges_iso[1:]) / 2,
    y=hist_iso,
    name='Isotropic sampling',
    opacity=0.5,
    marker=dict(color='salmon')
))

# Normal distribution for robustness_iso
'''fig.add_trace(go.Scatter(
    x=x_iso,
    y=y_iso,
    mode='lines',
    name=f"Normal (isotropic sampling)<br>µ={mean_iso:.2f}, σ={std_iso:.2f}",
    line=dict(color='red', dash='dash')
))'''



'''# Add vertical line for mean_sta
fig.add_trace(go.Scatter(
    x=[mean_sta, mean_sta],
    y=[0, max(y_sta) * 1.1],  # Extend slightly beyond the normal distribution peak for clarity
    mode="lines",
    name=f"Mean (STA): µ={mean_sta:.2f}",
    line=dict(color="blue", width=2)
))

# Add vertical line for mean_iso
fig.add_trace(go.Scatter(
    x=[mean_iso, mean_iso],
    y=[0, max(y_iso) * 1.1],  # Extend slightly beyond the normal distribution peak for clarity
    mode="lines",
    name=f"Mean (ISO): µ={mean_iso:.2f}",
    line=dict(color="red", width=2)
))'''

confidence = 95
sem_sta = st.sem(robustness_sta)
sem_iso = st.sem(robustness_isotropic)
# Calculate the 99% confidence interval
ci_sta = st.t.interval(confidence=confidence/100, df=len(robustness_sta) - 1, loc=mean_sta, scale=sem_sta)
ci_iso = st.t.interval(confidence=confidence/100, df=len(robustness_isotropic) - 1, loc=mean_iso, scale=sem_iso)

print(f"STA: 99% Confidence Interval: {ci_sta}")
print(f"ISO: 99% Confidence Interval: {ci_iso}")

'''# Add vertical lines for confidence intervals of STA
fig.add_trace(go.Scatter(
    x=[ci_sta[0], ci_sta[0]],
    y=[0, max(y_sta) * 1.1],
    mode="lines",
    # name=f"99% CI Lower (STA): {ci_sta[0]:.2f}",
    name=f"{confidence}% CI (STA): ({ci_sta[0]:.2f}, {ci_sta[1]:.2f})",
    line=dict(color="blue", width=2, dash="dash")
))

fig.add_trace(go.Scatter(
    x=[ci_sta[1], ci_sta[1]],
    y=[0, max(y_sta) * 1.1],
    mode="lines",
    name=f"99% CI Upper (STA): {ci_sta[1]:.2f}",
    showlegend=False,
    line=dict(color="blue", width=2, dash="dash")
))

# Add vertical lines for confidence intervals of ISO
fig.add_trace(go.Scatter(
    x=[ci_iso[0], ci_iso[0]],
    y=[0, max(y_iso) * 1.1],
    mode="lines",
    name=f"{confidence}% CI (isotropic sampling): ({ci_iso[0]:.2f}, {ci_iso[1]:.2f})",
    line=dict(color="red", width=2, dash="dash")
))

fig.add_trace(go.Scatter(
    x=[ci_iso[1], ci_iso[1]],
    y=[0, max(y_iso) * 1.1],
    mode="lines",
    name=f"99% CI Upper (ISO): {ci_iso[1]:.2f}",
    showlegend=False,
    line=dict(color="red", width=2, dash="dash")
))'''

# Update layout
fig.update_layout(
    #title="Distribution and Normal Fit of STA-based uniform and isotropic sampling",
    xaxis_title="Robustness",
    yaxis_title='Density',  # '"Probability Density",
    barmode='overlay',
    legend=dict(x=0.7, y=0.9, font=dict(size=16)),
    template="plotly_white",
    xaxis=dict(title_font=dict(size=20), tickfont=dict(size=16)),
    yaxis=dict(title_font=dict(size=20), tickfont=dict(size=16))
)


fig.write_image("sta_vs_isotropic_sampling_simglucose.pdf", width=1000, height=400, scale=2)
# Show the plot
fig.show()
