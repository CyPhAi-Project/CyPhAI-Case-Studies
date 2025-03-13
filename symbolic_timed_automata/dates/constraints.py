from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint
from syma.constraint.node.node import *
from syma.volume.constraint_abstraction import ConstraintAbstraction
from syma.volume.polyhedron_abstraction import PolyhedronAbstraction

#Constraints
r1 = VariableNode('v1')
r2 = VariableNode('v2')
sta = SymbolicTimedAutomaton(clocks="x", invariants="")

sta.add_var("v1", [0, 2])
sta.add_var("v2", [0, 2])

c_a = RealConstraint(
        formula=LEQNode(
            AddNode(r1, r2),
            ConstantNode(1.0)),
        alphabet=sta.alphabet
)

c_b1 = RealConstraint(
    alphabet=sta.alphabet,
    formula=AndNode(
        GEQNode(
            MinusNode(r1, r2),
            ConstantNode(1.0)
        ),
        AndNode(
            AndNode(
                LEQNode(ConstantNode(1), r1),
                LEQNode(r1, ConstantNode(2))
            ),
            AndNode(
                LEQNode(ConstantNode(0), r2),
                LEQNode(r2, ConstantNode(1))
            )
        )
    )
)

c_b2 = RealConstraint(
    alphabet=sta.alphabet,
    formula=AndNode(
        LEQNode(
            MinusNode(r1, r2),
            ConstantNode(1.0)
        ),
        AndNode(
            AndNode(
                LEQNode(ConstantNode(1), r1),
                LEQNode(r1, ConstantNode(2))
            ),
            AndNode(
                LEQNode(ConstantNode(0), r2),
                LEQNode(r2, ConstantNode(1))
            )
        )
    )
)

c_b3 = RealConstraint(
    alphabet=sta.alphabet,
    formula=AndNode(
        LEQNode(
            AddNode(r1, r2),
            ConstantNode(3.0)
        ),
        AndNode(
            AndNode(
                LEQNode(ConstantNode(1), r1),
                LEQNode(r1, ConstantNode(2))
            ),
            AndNode(
                LEQNode(ConstantNode(1), r2),
                LEQNode(r2, ConstantNode(2))
            )
        )
    )
)

c_b4 = RealConstraint(
    alphabet=sta.alphabet,
    formula=AndNode(
        GEQNode(
            MinusNode(
                r2,
                MulNode(r1, ConstantNode(2))
            ),
            ConstantNode(0)
        ),
        GEQNode(
            MinusNode(
                AddNode(
                    r2,
                    MulNode(r1, ConstantNode(2))
                ),
                ConstantNode(2)
            ),
            ConstantNode(0),
        )
    )
)

c_b5 = RealConstraint(
    alphabet=sta.alphabet,
    formula=AndNode(
        LEQNode(r1, ConstantNode(1)),
        AndNode(
            LEQNode(
                MinusNode(
                    r2,
                    MulNode(ConstantNode(2), r1)
                ),
                ConstantNode(0)
            ),
            GEQNode(
                MinusNode(
                    AddNode(
                        r2,
                        MulNode(ConstantNode(2), r1)
                    ),
                    ConstantNode(2)
                ),
                ConstantNode(0),
            )
        )
    )
)

constraints: list[RealConstraint] = [
    c_a,
    c_b1, c_b2, c_b3,
    c_b4,
    c_b5]
abstractions: list[PolyhedronAbstraction] = [PolyhedronAbstraction(['v1', 'v2'], [(0, 2), (0,2)], constr)
                for constr in constraints]

for ab in abstractions:
    ab.compute_abstraction()

