# Installation

Install required Python packages in `requirements.txt` (requires `cmake`).

## Sampling with Symbolic Timed Automata
Follow the instructions in ```lib/README.md```


# Runtime Monitoring

Run the following command to collect traces from `simglucose` and calculate the robustness interval over the observed blood glucose trace by `stlrom`.
The script is tested with Python 3.11

```bash
python monitor_robustness.py
```
This script will print out the robustness interval.

# Falsification

Run the following command to collect traces from `simglucose` and try to violate STL spec by searching for a scenario (i.e., a list of (time, meal size)) using `psy-taliro`.
The script is tested with Python 3.11

```bash
python falsify_robustness.py
```
This script will visualize the simulation traces in `out/bg.jpeg`


# Runtime monitoring with Symbolic Timed Automata for input generation
The script is tested with Python 3.10

```bash
python monitor_robustness_sta.py
```
