from symbolic_timed_automata.two_ears.sample_two_ears import sample_isotropic

signals = sample_isotropic(length=2, n_signals=10000)

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