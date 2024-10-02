from typing import Dict, Tuple

from syma.automaton.automaton import Location, SymbolicTimedAutomaton
from syma.constraint.constraint import Constraint, RealConstraint

from syma.constraint.node.node import Node, VariableNode, AddNode, GreaterNode, ConstantNode, EqualNode, AndNode, GEQNode, LEQNode, LessNode, OrNode, TrueNode, MulNode, MinusNode

from syma.automaton.automaton import sta_product
from syma.volume.estimator import volume_estimate

from syma.volume.polyhedron_abstraction import PolyhedronAbstraction

inputs={
        # Meal times and sizes defined for RandomScenario in simglucose
        # Bound on meal size is (mu-3*sigma, mu+3*sigma)
        "breakfast_time": (5, 9), "breakfast_size": (45-3*10, 45+3*10),
        "snack1_time": (9, 11), "snack1_size": (10-3*5, 10+3*5),
        "lunch_time": (12, 15), "lunch_size": (70-3*10, 70+3*10),
        "snack2_time": (14, 16), "snack2_size": (10-3*5, 10+3*5),
        "dinner_time": (16, 20), "dinner_size": (80-3*10, 80+3*10),
        "snack3_time": (20, 23), "snack3_size": (10-3*5, 10+3*5),
    }

def build_sa():
    # Automaton "C", manages the sum constraint
    sta = SymbolicTimedAutomaton(clocks="h,d,t", invariants="")

    # Variables
    sta.add_var("m", [0, 110])
    sta.add_var("m1", [0, 25])
    sta.add_var("m2", [0, 25])

    MAX_SUM_SNACKS = 40.0

    # locations
    b = Location("b", initial=True, final=True)
    s1 = Location("s1", initial=False, final=False)
    l = Location("l", initial=False, final=False)
    s2 = Location("s2", initial=False, final=False)
    d = Location("d", initial=False, final=False)


    sta.add_location(b)
    sta.add_location(s1)
    sta.add_location(l)
    sta.add_location(s2)
    sta.add_location(d)

    # Constraints
    var_node_m = VariableNode('m')
    var_node_m1 = VariableNode('m1')
    var_node_m2 = VariableNode('m2')

    var_names = list(sta.alphabet.vars)
    var_bounds = [sta.alphabet.vars_domain[var_name] for var_name in var_names]




    no_snack_node = LEQNode(AddNode(var_node_m1, var_node_m2), ConstantNode(1.0))

    only_snack_2_node = AndNode(
        LEQNode(var_node_m1, ConstantNode(1.0)),
        GEQNode(var_node_m2, ConstantNode(5.0)))
    tot_snack_node = AndNode(
            LEQNode(
                AddNode(var_node_m1, var_node_m2),
                ConstantNode(MAX_SUM_SNACKS)
            ),
            AndNode(
                GEQNode(var_node_m1, ConstantNode(5.0)),
                GEQNode(var_node_m2, ConstantNode(5.0)))
        )

    def main_meal_bounds(lb: float, ub: float):
        return AndNode(
            GEQNode(var_node_m, ConstantNode(lb)),
            LEQNode(var_node_m, ConstantNode(ub))
        )

    # have breakfast and go to need snack
    sta.add_transition(
        source=b,
        target=s1,
        constraint=RealConstraint(
            formula=AndNode(
                main_meal_bounds(inputs["breakfast_size"][0], inputs["breakfast_size"][1]),
                no_snack_node),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time'][0]})&(h<={inputs['breakfast_time'][1]})",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="to_snack_1"
    )

    # have breakfast and go to need lunch
    sta.add_transition(
        source=b,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(main_meal_bounds(inputs["breakfast_size"][0], inputs["breakfast_size"][1]),
                            only_snack_2_node),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time'][0]})&(h<={inputs['breakfast_time'][1]})",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="to_lunch"
    )

    # have snack and go to need lunch
    sta.add_transition(
        source=s1,
        target=l,
        constraint=RealConstraint(
            formula=AndNode(tot_snack_node,main_meal_bounds(0.0, 1.0)),
            alphabet=sta.alphabet),
        time_constraint="(h>=9)&(h<=11)",
        clock_resets="t",
        abstraction_type=PolyhedronAbstraction,
        label="snack_to_lunch"
    )

    # have lunch and go to need snack
    sta.add_transition(
        source=l,
        target=s2,
        constraint=RealConstraint(
            formula=AndNode(main_meal_bounds(inputs["lunch_size"][0], inputs["lunch_size"][1]),no_snack_node),
            alphabet=sta.alphabet),
        time_constraint="(h>=12)&(h<=15)&(d>=4)&(d<=6)",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="to_snack_2"
    )

    # have lunch and go to need dinner
    sta.add_transition(
        source=l,
        target=d,
        constraint=RealConstraint(
            formula=AndNode(main_meal_bounds(inputs["lunch_size"][0], inputs["lunch_size"][1]),
                            no_snack_node),
            alphabet=sta.alphabet),
        time_constraint="(h>=12)&(h<=15)&(d>=4)&(d<=6)",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="to_dinner"
    )

    # have second snack and go to have dinner
    sta.add_transition(
        source=s2,
        target=d,
        constraint=RealConstraint(
            formula=AndNode(tot_snack_node,main_meal_bounds(0.0, 1.0)),
            alphabet=sta.alphabet),
        time_constraint="(h>=15)&(h<=18)",
        clock_resets="t",
        abstraction_type=PolyhedronAbstraction,
        label="snack_to_dinner"
    )

    # have dinner and go to have breakfast
    sta.add_transition(
        source=d,
        target=b,
        constraint=RealConstraint(
            formula=AndNode(main_meal_bounds(inputs["dinner_size"][0], inputs["dinner_size"][1]),no_snack_node),
            alphabet=sta.alphabet),
        time_constraint="(h>=19)&(h<=22)&(d>=5)&(d<=7)",#&(t>=2)&(t<=4)",
        clock_resets="d,t,h",
        abstraction_type=PolyhedronAbstraction,
        label="to_breakfast"
    )





    volume_dict, abstraction_dict = volume_estimate(sta)

    sta_prism, constraints_mapping = sta.to_prism(volume_dict, visible_sym_constraints=False)
    sta_prism_constr, _ = sta.to_prism(volume_dict, visible_sym_constraints=True)

    return sta, volume_dict, abstraction_dict, constraints_mapping, sta_prism, sta_prism_constr, var_names, var_bounds
