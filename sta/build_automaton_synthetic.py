from typing import Dict, Tuple

from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import Node, VariableNode, AddNode, GreaterNode, ConstantNode, EqualNode, AndNode, GEQNode, LEQNode, LessNode, OrNode, TrueNode, MulNode, MinusNode

from syma.volume.hyperrectangle_abstraction import HyperrectangleAbstraction

from sta.lib.syma.syma.volume.polyhedron_abstraction import PolyhedronAbstraction


def build_sta() -> SymbolicTimedAutomaton:
    # Automaton "C", manages the sum constraint
    sta = SymbolicTimedAutomaton(clocks="x,y", invariants="")

    # Variables
    sta.add_var("v1", [0, 1])
    sta.add_var("v2", [0, 1])
    sta.add_var("v3", [0, 1])

    # locations
    l = Location("l", initial=True, final=True)

    sta.add_location(l)

    # Constraints
    n1 = VariableNode('v1')
    n2 = VariableNode('v2')
    n3 = VariableNode('v3')

    order1 = AndNode(
        GEQNode(n1,n2),
        GEQNode(n2, n3)
    )

    order2 = AndNode(
        LEQNode(n1,n2),
        LEQNode(n2, n3)
    )

    sum_node_a = AddNode(
        n1,
        AddNode(n2, n3)
    )

    # a: (v1 >= v2 >= v3) AND (v1+v2+v3) <= 1
    sta.add_transition(
        source=l,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(
                order1,
                LEQNode(
                    sum_node_a, ConstantNode(1.0)
                )
            ),
            alphabet=sta.alphabet),
        time_constraint=f"(x<1)&(y<1)",
        clock_resets="y",
        abstraction_type=PolyhedronAbstraction,
        label="a"
    )

    sum_node_b = AddNode(
        MulNode(ConstantNode(3.0), n1),
        AddNode(
            MulNode(ConstantNode(2.0), n2),
            n3
        )
    )

    # b: (v1 <= v2 <= v3) AND 0.5<=(3v1+2v2+v3) <= 1
    sta.add_transition(
        source=l,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(
                order2,
                AndNode(
                    LEQNode(
                        ConstantNode(0.5), sum_node_b
                    ),
                    LEQNode(
                        sum_node_b, ConstantNode(1.5)
                    )
                )
            ),
            alphabet=sta.alphabet),
        time_constraint=f"(x<1)&(y<1)",
        clock_resets="x",
        abstraction_type=PolyhedronAbstraction,
        label="b"
    )

    # c (v1 <= v2 <= v3) AND 0.5<=(3v1+2v2+v3) <= 1
    sta.add_transition(
        source=l,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(
                AndNode(
                    LEQNode(ConstantNode(0.7), sum_node_a),
                    LEQNode(sum_node_a, ConstantNode(2.0))
                ),
                AndNode(
                    AndNode(
                        LEQNode(
                            ConstantNode(0.05), MinusNode(n2, n1)
                        ),
                        LEQNode(
                            MinusNode(n2, n1), ConstantNode(0.1)
                        )
                    ),
                    AndNode(
                        LEQNode(
                            ConstantNode(0.05), MinusNode(n2, n3)
                        ),
                        LEQNode(
                            MinusNode(n2, n3), ConstantNode(0.1)
                        )
                    )
                )
            ),
            alphabet=sta.alphabet),
        time_constraint=f"(x<1)&(y<1)",
        clock_resets="x,y",
        abstraction_type=PolyhedronAbstraction,
        label="c"
    )

    sta.build()
    return sta
