#!/bin/bash

#6. NOMAD with black-box constraints

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_nomad_constrained.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nomad_constrained -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nomad_constrained/log.txt

#8. Nevergrad with black-box constraints

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_nevergrad_constrained.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nevergrad_constrained -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nevergrad_constrained/log.txt
