#!/bin/bash

# 2. Uniform Random Sampling with STA

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/random/uniform_sampling_sta.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/uniform_sta -i 1000 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/uniform_sta/log.txt

# 4. Staliro with penalties

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_staliro_penalties.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_penalties -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_penalties/log.txt