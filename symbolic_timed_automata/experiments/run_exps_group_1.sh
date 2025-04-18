#!/bin/bash

# 1. Random Isotropic Sampling

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/random/falsify_isotropic_sampling.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/isotropic -i 1000 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/isotropic/log.txt

# 3. Staliro unconstrained

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_staliro_unconstrained.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_unconstrained -i 500 -r 100 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_unconstrained/log.txt