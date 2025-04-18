#!/bin/bash

#5. Staliro with STA

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_staliro_sta.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_sta -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/staliro_sta/log.txt

#7. NOMAD with STA

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_nomad_sta.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nomad_sta -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nomad_sta/log.txt

#9. Nevergrad with STA

time python3 /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/simglucose/falsification/falsify_nevergrad_sta.py -o /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nevergrad_sta -i 500 -r 10 > /home/marco/work/research/dev/CyPhAI-Case-Studies/symbolic_timed_automata/experiments/output/simglucose/falsification/nevergrad_sta/log.txt
