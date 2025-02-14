from syma.automaton.automaton import Location
from syma.automaton.symbolic_timed_automaton import SymbolicTimedAutomaton
from syma.constraint.constraint import RealConstraint

from syma.constraint.node.node import VariableNode, ConstantNode, AndNode, GEQNode, LEQNode

from syma.volume.hyperrectangle_abstraction import HyperrectangleAbstraction
from syma.volume.polyhedron_abstraction import PolyhedronAbstraction

from symbolic_timed_automata.simglucose.params import get_meal_space

def build_sa_three_snacks(dist_factor: float) -> SymbolicTimedAutomaton:

    inputs = get_meal_space(dist_factor)

    sta = SymbolicTimedAutomaton(clocks="h,d,t", invariants="")

    # Variables
    sta.add_var("m", [0, 110])
    sta.add_var("m_dummy", [0, 110])

    # locations
    b = Location("b", initial=True, final=True)
    s1 = Location("s1", initial=False, final=False)
    l = Location("l", initial=False, final=False)
    l_no_s1 = Location("l_no_s1", initial=False, final=False)
    s2 = Location("s2", initial=False, final=False)
    d = Location("d", initial=False, final=False)
    s3 = Location("s3", initial=False, final=False)


    sta.add_location(b)
    sta.add_location(s1)
    sta.add_location(l)
    sta.add_location(l_no_s1)
    sta.add_location(s2)
    sta.add_location(d)
    sta.add_location(s3)

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
            formula=meal_bounds(inputs["breakfast_size_with_snack1"][0], inputs["breakfast_size_with_snack1"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time_with_snack1'][0]})&(h<={inputs['breakfast_time_with_snack1'][1]})",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="breakfast_to_snack_1"
    )

    # have breakfast and go to need lunch (skip snack 1)
    sta.add_transition(
        source=b,
        target=l_no_s1,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["breakfast_size_no_snack1"][0], inputs["breakfast_size_no_snack1"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['breakfast_time_no_snack1'][0]})&(h<={inputs['breakfast_time_no_snack1'][1]})",
        clock_resets="d,t",
        abstraction_type=HyperrectangleAbstraction,
        label="breakfast_to_lunch"
    )

    # have snack 1 and go to need lunch
    sta.add_transition(
        source=s1,
        target=l,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["snack1_size"][0], inputs["snack1_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['snack1_time'][0]})&(h<={inputs['snack1_time'][1]})",
        clock_resets="t",
        abstraction_type=HyperrectangleAbstraction,
        label="snack_1_to_lunch"
    )

    # have lunch (having had snack 1) and go to need snack 2
    sta.add_transition(
        source=l,
        target=s2,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size_with_snack1_and_2"][0], inputs["lunch_size_with_snack1_and_2"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['lunch_time'][0]})"
                        f"&(h<={inputs['lunch_time'][1]})"
                        f"&(d>={inputs['lunch_d_with_snack1'][0]})"
                        f"&(d<={inputs['lunch_d_with_snack1'][1]})",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="lunch_to_snack_2_with_s1"
    )

    # have lunch (having had snack 1) and go to need dinner (skip snack 2)
    sta.add_transition(
        source=l,
        target=d,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size_with_snack1_no_snack2"][0], inputs["lunch_size_with_snack1_no_snack2"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['lunch_time'][0]})"
                        f"&(h<={inputs['lunch_time'][1]})"
                        f"&(d>={inputs['lunch_d_with_snack1'][0]})"
                        f"&(d<={inputs['lunch_d_with_snack1'][1]})",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="lunch_with_snack_1_to_dinner"
    )

    # have lunch (without having had snack 1) and go to need snack 2)
    sta.add_transition(
        source=l_no_s1,
        target=s2,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["lunch_size_no_snack1_with_snack2"][0], inputs["lunch_size_no_snack1_with_snack2"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['lunch_time'][0]})"
                        f"&(h<={inputs['lunch_time'][1]})"
                        f"&(d>={inputs['lunch_d_no_snack1'][0]})"
                        f"&(d<={inputs['lunch_d_no_snack1'][1]})",
        clock_resets="d,t",
        abstraction_type=PolyhedronAbstraction,
        label="lunch_to_snack_2_no_snack_1"
    )

    # have snack 2 and go to have dinner
    sta.add_transition(
        source=s2,
        target=d,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["snack2_size"][0], inputs["snack2_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['snack2_time'][0]})"
                        f"&(h<={inputs['snack2_time'][1]})",
        clock_resets="t",
        abstraction_type=PolyhedronAbstraction,
        label="snack_2_to_dinner"
    )

    # Have dinner and go to breakfast (skip snack 3)
    sta.add_transition(
        source=d,
        target=b,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["dinner_size_no_snack3"][0], inputs["dinner_size_no_snack3"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['dinner_time_no_snack3'][0]})"
                        f"&(h<={inputs['dinner_time_no_snack3'][1]})"
                        f"&(d>={inputs['dinner_d_no_snack3'][0]})"
                        f"&(d<={inputs['dinner_d_no_snack3'][1]})",
        clock_resets="d,h,t",
        abstraction_type=HyperrectangleAbstraction,
        label="dinner_to_breakfast_no_snack_3"
    )

    # Have dinner and go to need snack 3
    sta.add_transition(
        source=d,
        target=s3,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["dinner_size_with_snack3"][0], inputs["dinner_size_with_snack3"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['dinner_time_with_snack3'][0]})"
                        f"&(h<={inputs['dinner_time_with_snack3'][1]})"
                        f"&(d>={inputs['dinner_d_with_snack3'][0]})"
                        f"&(d<={inputs['dinner_d_with_snack3'][1]})",
        clock_resets="t",
        abstraction_type=HyperrectangleAbstraction,
        label="dinner_to_snack_3"
    )

    sta.add_transition(
        source=s3,
        target=b,
        constraint=RealConstraint(
            formula=meal_bounds(inputs["snack3_size"][0], inputs["snack3_size"][1]),
            alphabet=sta.alphabet),
        time_constraint=f"(h>={inputs['snack3_time'][0]})"
                        f"&(h<={inputs['snack3_time'][1]})",
        clock_resets="d,h,t",
        abstraction_type=HyperrectangleAbstraction,
        label="snack3_to_breakfast"
    )

    sta.build()
    return sta #, volume_dict, abstraction_dict, constraints_mapping, sta_prism, sta_prism_constr, var_names, var_bound
