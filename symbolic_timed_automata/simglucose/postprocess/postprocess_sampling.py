import json
import scipy.stats as st

path = "../../../out/sampling/sta"

with open(f"{path}/1/dump.json", "r") as f:
    res_sta = json.load(f)

robustness_sta = res_sta['evaluations']

with open(f"../../../out/sampling/rejection/1/dump.json", "r") as f:
    res_naive = json.load(f)

robustness_rej = res_naive['evaluations']

import numpy as np
import plotly.graph_objects as go

# Compute mean and standard deviation for both lists
mean_sta = np.mean(robustness_sta)
std_sta = np.std(robustness_sta)

mean_rej = np.mean(robustness_rej)
std_rej = np.std(robustness_rej)

# Generate normal distribution for both lists
x_sta = np.linspace(min(robustness_sta) - 1, max(robustness_sta) + 1, 500)
y_sta = (1 / (std_sta * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_sta - mean_sta) / std_sta) ** 2)

x_rej = np.linspace(min(robustness_rej) - 1, max(robustness_rej) + 1, 500)
y_rej = (1 / (std_rej * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_rej - mean_rej) / std_rej) ** 2)

# Bin data
bins_sta = np.histogram_bin_edges(robustness_sta, bins=50)
bins_rej = np.histogram_bin_edges(robustness_rej, bins=50)

hist_sta, bin_edges_sta = np.histogram(robustness_sta, bins=bins_sta, density=True)
hist_rej, bin_edges_rej = np.histogram(robustness_rej, bins=bins_rej, density=True)

# Create the histogram and normal distribution plots
fig = go.Figure()

# Bar for robustness_sta
fig.add_trace(go.Bar(
    x=(bin_edges_sta[:-1] + bin_edges_sta[1:]) / 2,
    y=hist_sta,
    name='STA',
    opacity=0.6,
    marker=dict(color='lightblue')
))

# Normal distribution for robustness_sta
fig.add_trace(go.Scatter(
    x=x_sta,
    y=y_sta,
    mode='lines',
    name=f"Normal (STA)<br>µ={mean_sta:.2f}, σ={std_sta:.2f}",
    line=dict(color='blue', dash='dash')
))

# Bar for robustness_rej
fig.add_trace(go.Bar(
    x=(bin_edges_rej[:-1] + bin_edges_rej[1:]) / 2,
    y=hist_rej,
    name='Rejection sampling',
    opacity=0.6,
    marker=dict(color='salmon')
))

# Normal distribution for robustness_rej
fig.add_trace(go.Scatter(
    x=x_rej,
    y=y_rej,
    mode='lines',
    name=f"Normal (Rejection sampling)<br>µ={mean_rej:.2f}, σ={std_rej:.2f}",
    line=dict(color='red', dash='dash')
))



'''# Add vertical line for mean_sta
fig.add_trace(go.Scatter(
    x=[mean_sta, mean_sta],
    y=[0, max(y_sta) * 1.1],  # Extend slightly beyond the normal distribution peak for clarity
    mode="lines",
    name=f"Mean (STA): µ={mean_sta:.2f}",
    line=dict(color="blue", width=2)
))

# Add vertical line for mean_rej
fig.add_trace(go.Scatter(
    x=[mean_rej, mean_rej],
    y=[0, max(y_rej) * 1.1],  # Extend slightly beyond the normal distribution peak for clarity
    mode="lines",
    name=f"Mean (REJ): µ={mean_rej:.2f}",
    line=dict(color="red", width=2)
))'''

confidence = 95
sem_sta = st.sem(robustness_sta)
sem_rej = st.sem(robustness_rej)
# Calculate the 99% confidence interval
ci_sta = st.t.interval(confidence=confidence/100, df=len(robustness_sta) - 1, loc=mean_sta, scale=sem_sta)
ci_rej = st.t.interval(confidence=confidence/100, df=len(robustness_rej) - 1, loc=mean_rej, scale=sem_rej)

print(f"STA: 99% Confidence Interval: {ci_sta}")
print(f"REJ: 99% Confidence Interval: {ci_rej}")

# Add vertical lines for confidence intervals of STA
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

# Add vertical lines for confidence intervals of REJ
fig.add_trace(go.Scatter(
    x=[ci_rej[0], ci_rej[0]],
    y=[0, max(y_rej) * 1.1],
    mode="lines",
    name=f"{confidence}% CI (Rejection sampling): ({ci_rej[0]:.2f}, {ci_rej[1]:.2f})",
    line=dict(color="red", width=2, dash="dash")
))

fig.add_trace(go.Scatter(
    x=[ci_rej[1], ci_rej[1]],
    y=[0, max(y_rej) * 1.1],
    mode="lines",
    name=f"99% CI Upper (REJ): {ci_rej[1]:.2f}",
    showlegend=False,
    line=dict(color="red", width=2, dash="dash")
))

# Update layout
fig.update_layout(
    title="Distribution and Normal Fit of STA-based uniform and rejection sampling",
    xaxis_title="Robustness",
    yaxis_title='Density',  # '"Probability Density",
    barmode='overlay',
    legend=dict(x=0.1, y=0.9, font=dict(size=16)),
    template="plotly_white",
    xaxis=dict(title_font=dict(size=20), tickfont=dict(size=16)),
    yaxis=dict(title_font=dict(size=20), tickfont=dict(size=16))
)



# Show the plot
fig.show()
