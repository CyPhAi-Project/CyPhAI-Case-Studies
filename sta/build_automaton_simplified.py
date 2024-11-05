from typing import Dict, Tuple

from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import Node, VariableNode, AddNode, GreaterNode, ConstantNode, EqualNode, AndNode, GEQNode, LEQNode, LessNode, OrNode, TrueNode, MulNode, MinusNode

from syma.volume.hyperrectangle_abstraction import HyperrectangleAbstraction

# from syma.volume.polyhedron_abstraction import PolyhedronAbstraction
DIST_FACTOR = 0.1

inputs={
        # Meal times and sizes defined for RandomScenario in simglucose
        # Bound on meal size is (mu-3*sigma, mu+3*sigma)
        "breakfast_time": (5, 9), "breakfast_size": (45-(3*10)*DIST_FACTOR, 45+(3*10)*DIST_FACTOR),
        "snack1_time": (9, 11), "snack1_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
        "lunch_time": (12, 15), "lunch_size": (70-(3*10)*DIST_FACTOR, 70+(3*10)*DIST_FACTOR),
        "snack2_time": (14, 16), "snack2_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
        "dinner_time": (16, 20), "dinner_size": (80-(3*10)*DIST_FACTOR, 80+(3*10)*DIST_FACTOR),
        "snack3_time": (20, 23), "snack3_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),
    }

'''inputs={
        # Meal times and sizes defined for RandomScenario in simglucose
        # Bound on meal size is (mu-3*sigma, mu+3*sigma)
        "breakfast_time": (5, 9), "breakfast_size": (45-1, 45+1),
        "snack1_time": (9, 11), "snack1_size": (10-1, 10+1),
        "lunch_time": (12, 15), "lunch_size": (70-1, 70+1),
        "snack2_time": (14, 16), "snack2_size": (10-1, 10+1),
        "dinner_time": (16, 20), "dinner_size": (80-1, 80+1),
        "snack3_time": (20, 23), "snack3_size": (10-1, 10+1),
    }'''

def build_sa() -> SymbolicTimedAutomaton:
    # Automaton "C", manages the sum constraint
    sta = SymbolicTimedAutomaton(clocks="h,d,t", invariants="")

    # Variables
    sta.add_var("m", [0, 110])

    # locations
    b = Location("b", initial=True, final=True)
    s1 = Location("s1", initial=False, final=False)
    l = Location("l", initial=False, final=False)
    l_no_s1 = Location("l_no_s1", initial=False, final=False)
    s2 = Location("s2", initial=False, final=False)
    d = Location("d", initial=False, final=False)


    sta.add_location(b)
    sta.add_location(s1)
    sta.add_location(l)
    sta.add_location(l_no_s1)
    sta.add_location(s2)
    sta.add_location(d)

    # Constraints
    var_node_m = VariableNode('m')


    def meal_bounds(lb: float, ub: float):
        return AndNode(
            GEQNode(var_node_m, ConstantNode(lb)),
            LEQNode(var_node_m, ConstantNode(ub))
        )

    # have breakfast and go to need snack 1
    sta.add_transition(
        source=b,
        target=s1,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["breakfast_size"][0], inputs["breakfast_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time'][0]})&(h<={inputs['breakfast_time'][1]})",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_snack_1"
    )

    # have breakfast and go to need lunch
    sta.add_transition(
        source=b,
        target=l_no_s1,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["breakfast_size"][0], inputs["breakfast_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time'][0]})&(h<={inputs['breakfast_time'][1]})",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_lunch"
    )

    # have snack and go to need lunch
    sta.add_transition(
        source=s1,
        target=l,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["snack1_size"][0], inputs["snack1_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['snack1_time'][0]})&(h<={inputs['snack1_time'][1]})",
        clock_resets="t",
        abstraction_type=HyperrectangleAbstraction,
        label="snack_to_lunch"
    )

    # have lunch (having had snack 1) and go to need snack 2
    sta.add_transition(
        source=l,
        target=s2,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size"][0], inputs["lunch_size"][1]),
            alphabet=sta.alphabet),
        time_constraint="(h>=12)&(h<=15)&(d>=4)&(d<=6)",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_snack_2_w_s1"
    )

    # have lunch (having had snack 1) and go to need dinner
    sta.add_transition(
        source=l,
        target=d,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size"][0], inputs["lunch_size"][1]),
            alphabet=sta.alphabet),
        time_constraint="(h>=12)&(h<=15)&(d>=4)&(d<=6)",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_dinner"
    )

    # have lunch (without having had snack 1) and go to need snack 2)
    sta.add_transition(
        source=l_no_s1,
        target=s2,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size"][0], inputs["lunch_size"][1]),
            alphabet=sta.alphabet),
        time_constraint="(h>=12)&(h<=15)&(d>=4)&(d<=6)",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_snack_2_wo_s1"
    )

    # have snack 2 and go to have dinner
    sta.add_transition(
        source=s2,
        target=d,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["snack2_size"][0], inputs["snack2_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['snack2_time'][0]})&(h<={inputs['snack2_time'][1]})",
        clock_resets="t",
        abstraction_type=HyperrectangleAbstraction,
        label="snack_to_dinner"
    )

    sta.add_transition(
        source=d,
        target=b,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["dinner_size"][0], inputs["dinner_size"][1]),
            alphabet=sta.alphabet),
        time_constraint="(h>=19)&(h<=22)&(d>=5)&(d<=7)",#&(t>=2)&(t<=4)",
        clock_resets="d,h,t",
        abstraction_type=HyperrectangleAbstraction,
        label="to_breakfast"
    )

    # volume_dict, abstraction_dict = volume_estimate(sta)

    # sta_prism, constraints_mapping = sta.to_prism(volume_dict, visible_sym_constraints=False)
    # sta_prism_constr, _ = sta.to_prism(visible_sym_constraints=True)

    sta.build()
    return sta #, volume_dict, abstraction_dict, constraints_mapping, sta_prism, sta_prism_constr, var_names, var_bounds
