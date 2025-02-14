from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import VariableNode, AddNode, ConstantNode, LEQNode

from symbolic_timed_automata.lib.syma.syma.volume.polyhedron_abstraction import PolyhedronAbstraction

CLOCK_UB = 1
def build_one_ear_sta() -> SymbolicTimedAutomaton:
    sta = SymbolicTimedAutomaton(clocks="x,y", invariants="")

    # Variables
    sta.add_var("v1", [0, 2])
    sta.add_var("v2", [0, 2])

    # locations
    l = Location("l", initial=True, final=True)

    sta.add_location(l)

    # Constraints
    n1 = VariableNode('v1')
    n2 = VariableNode('v2')

    # a:
    sta.add_transition(
        source=l,
        target=l,
        constraint=RealConstraint(
            formula=LEQNode(
                AddNode(n1, n2),
                ConstantNode(1.0)),
            alphabet=sta.alphabet),
        time_constraint=f"(x<{CLOCK_UB})&(y<{CLOCK_UB})",
        clock_resets="y",
        abstraction_type=PolyhedronAbstraction,
        label="a"
    )

    sta.build()
    return sta