from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import Node, VariableNode, AddNode, GreaterNode, ConstantNode, EqualNode, AndNode, GEQNode, LEQNode, LessNode, OrNode, TrueNode, MulNode, MinusNode

from syma.volume.polyhedron_abstraction import PolyhedronAbstraction

CLOCK_UB = 1
def build_two_ears_sta() -> SymbolicTimedAutomaton:
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

    # b: 2*v_1 + v_2 ≥ 2 ∧ v_1 + v_2 ≤ 3
    sta.add_transition(
        source=l,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(
                GEQNode(
                    AddNode(
                        MulNode(ConstantNode(2.0), n1),
                        n2),
                    ConstantNode(2.0)),
                LEQNode(
                    AddNode(n1, n2),
                    ConstantNode(3.0))
            )            ,
            alphabet=sta.alphabet),
        time_constraint=f"(x<{CLOCK_UB})&(y<{CLOCK_UB})",
        clock_resets="x",
        abstraction_type=PolyhedronAbstraction,
        label="b"
    )

    sta.build()
    return sta