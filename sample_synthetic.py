from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton

from sta.build_automaton_synthetic import build_sta
from sta.input_generator import InputGenerator
import random

STA_OUT_FNAME = "sta/output/synthetic/sta.prism"
ABSTRACT_TRAJ_FNAME = "sta/output/synthetic/abstract_trajectories.json"
CONCRETE_TRAJ_FNAME = "sta/output/synthetic/concrete_trajectories.json"


def main():
    sta: SymbolicTimedAutomaton = build_sta()

    sta_input_gen: InputGenerator = InputGenerator(sta, STA_OUT_FNAME, "sta/lib/wordgen", length=5)


def sample(length: int = 6):
    l = 0
    actions = []
    delays = []
    t = 0
    while l < length:
        if t == 0:
            if random.random() < 0.5:
                action = 0
            else:
                action = 1
        else:
            if random.random() < 1 - t:
                action = actions[-1]
                d = random.random()
                while d >= 1 -t:
                    d = random.random()
                delay = d
            else:
                action = 1 - actions[-1]
                delay = random.random()


if __name__ == "__main__":
    main()
