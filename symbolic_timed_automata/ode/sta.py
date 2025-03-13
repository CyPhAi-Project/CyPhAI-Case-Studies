from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import Node, VariableNode, AddNode, GreaterNode, ConstantNode, EqualNode, AndNode, GEQNode, LEQNode, LessNode, OrNode, TrueNode, MulNode, MinusNode

from syma.volume.polyhedron_abstraction import PolyhedronAbstraction

CLOCK_UB = 1
def build_ode_sta() -> SymbolicTimedAutomaton:
    sta = SymbolicTimedAutomaton(clocks="x,y", invariants="")

    # Variables
    sta.add_var("v1", [0, 1])
    sta.add_var("v2", [0, 1])

    # locations
    l1 = Location("l1", initial=True, final=True)
    l2 = Location("l2", initial=False, final=True)

    sta.add_location(l1)
    sta.add_location(l2)

    # Constraints
    n1 = VariableNode('v1')
    n2 = VariableNode('v2')



    # a
    sta.add_transition(
        source=l1,
        target=l2,
        constraint=RealConstraint(
            formula=LEQNode(
                AddNode(n1, n2),
                ConstantNode(2.0)),
            alphabet=sta.alphabet),
        time_constraint=f"(x<5)&(y>1)&(y<3)",
        clock_resets="x",
        abstraction_type=PolyhedronAbstraction,
        label="a"
    )

    # b
    sta.add_transition(
        source=l2,
        target=l1,
        constraint=RealConstraint(
            formula=LEQNode(
                AddNode(n1, n2),
                ConstantNode(1.0)),
            alphabet=sta.alphabet),
        time_constraint=f"(x>1)&(x<3)&(y<5)",
        clock_resets="y",
        abstraction_type=PolyhedronAbstraction,
        label="b"
    )

    sta.build()
    return sta