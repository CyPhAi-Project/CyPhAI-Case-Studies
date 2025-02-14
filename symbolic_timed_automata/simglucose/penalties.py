from typing import Tuple

import staliro

MIN_SNACK = 5
BASE_PENALTY = 1000
error = 1e-5

def get_penalties(meal_space, meal_plan: staliro.Sample | dict[str, float]):
    if isinstance(meal_plan, dict):
        P = meal_plan
    else:
        P = meal_plan.static

    s1 = 0 if P["snack1_size"] < MIN_SNACK else P["snack1_size"]
    s2 = 0 if P["snack2_size"] < MIN_SNACK else P["snack2_size"]
    s3 = 0 if P["snack3_size"] < MIN_SNACK else P["snack3_size"]


    pen_snacks_12_ALO = snacks_12_at_least_one(P, s1, s2)

    pen_breakfast_time = breakfast_time(meal_space, P, s1)

    pen_breakfast_size = breakfast_size(meal_space, P, s1)

    pen_lunch_time = lunch_time(meal_space, P, s1)

    pen_lunch_size = lunch_size(meal_space, P, s1, s2)

    pen_dinner_time_h, pen_dinner_time_d = dinner_time(meal_space, P, s3)

    pen_dinner_size = dinner_size(meal_space, P, s3)

    return dict(
        snacks_12_ALO=pen_snacks_12_ALO,
        breakfast_time=pen_breakfast_time,
        breakfast_size=pen_breakfast_size,
        lunch_time=pen_lunch_time,
        lunch_size=pen_lunch_size,
        dinner_time_h=pen_dinner_time_h,
        dinner_time_d=pen_dinner_time_d,
        dinner_size=pen_dinner_size,
        total=pen_snacks_12_ALO+pen_breakfast_time+pen_breakfast_size+pen_lunch_time+pen_lunch_size+pen_dinner_time_h+pen_dinner_time_d+pen_dinner_size)

def snacks_12_at_least_one(P, s1, s2) -> float:
    # 1-2. At least one snack between morning and afternoon, and, if present, the size is at least MIN_SNACK
    if s1 + s2 == 0:
        pen_snacks_12_ALO = BASE_PENALTY + MIN_SNACK - max(P["snack1_size"], P["snack2_size"])
    else:
        pen_snacks_12_ALO = 0
    return pen_snacks_12_ALO

def breakfast_time(meal_space, P, s1) -> float:
    # 3. There is snack 1 if and only if the breakfast is between 5 and 8
    if s1 > 0 and P["breakfast_time"] > meal_space["breakfast_time_with_snack1"][1]:
        # breakfast too late
        pen_breakfast_time = BASE_PENALTY + P["breakfast_time"] - meal_space["breakfast_time_with_snack1"][1]
    elif s1 == 0 and P["breakfast_time"] < meal_space["breakfast_time_with_snack1"][0]:
        pen_breakfast_time = BASE_PENALTY + meal_space["breakfast_time_with_snack1"][0] - P["breakfast_time"]
    else:
        pen_breakfast_time = 0

    return pen_breakfast_time

def breakfast_size(meal_space, P, s1) -> float:
    # 4. There is snack 1 if and only if the breakfast size is coherent
    if s1 > 0 and P["breakfast_size"] > meal_space["breakfast_size_with_snack1"][1]:
        pen_breakfast_size = BASE_PENALTY + P["breakfast_size"] - meal_space["breakfast_size_with_snack1"][1]
    elif s1 == 0 and P["breakfast_size"] < meal_space["breakfast_size_no_snack1"][0]:
        pen_breakfast_size = BASE_PENALTY + meal_space["breakfast_size_no_snack1"][0] - P["breakfast_size"]
    else:
        pen_breakfast_size = 0
    return pen_breakfast_size

def lunch_time(meal_space, P, s1) -> float:
    # 5. If there is no snack 1, lunch must be between 3 and 6 hours from breakfast.
    #    If there is snack 1, lunch must be between 4 and 7 hours from breakfast
    if (s1 > 0) and P["lunch_time"] + error < P["breakfast_time"] + meal_space["lunch_d_with_snack1"][0]:
        pen_lunch_time = BASE_PENALTY + (P["breakfast_time"] + meal_space["lunch_d_with_snack1"][0]) - P["lunch_time"]
    elif (s1 > 0) and P["lunch_time"] - error > P["breakfast_time"] + meal_space["lunch_d_with_snack1"][1]:
        pen_lunch_time = BASE_PENALTY + P["lunch_time"] - (P["breakfast_time"] + meal_space["lunch_d_with_snack1"][1])
    elif (s1 == 0) and P["lunch_time"] + error < P["breakfast_time"] + meal_space["lunch_d_no_snack1"][0]:
        pen_lunch_time = BASE_PENALTY + (P["breakfast_time"] + meal_space["lunch_d_no_snack1"][0]) - P["lunch_time"]
    elif (s1 == 0) and P["lunch_time"] - error > P["breakfast_time"] + meal_space["lunch_d_no_snack1"][1]:
        pen_lunch_time = BASE_PENALTY + P["lunch_time"] - (P["breakfast_time"] + meal_space["lunch_d_no_snack1"][1])
    else:
        pen_lunch_time = 0
    return pen_lunch_time

def lunch_size(meal_space, P, s1, s2) -> float:
    # 6. Size of lunch depending on snack 1 and snack 2
    if s1 > 0 and s2 == 0:
        if P["lunch_size"] < meal_space["lunch_size_with_snack1_no_snack2"][0]:
            pen_lunch_size = BASE_PENALTY + meal_space["lunch_size_with_snack1_no_snack2"][0] - P["lunch_size"]
        elif P["lunch_size"] > meal_space["lunch_size_with_snack1_no_snack2"][1]:
            pen_lunch_size = BASE_PENALTY + P["lunch_size"] - meal_space["lunch_size_with_snack1_no_snack2"][1]
        else:
            pen_lunch_size = 0
    elif s1 == 0 and s2 > 0:
        if P["lunch_size"] < meal_space["lunch_size_no_snack1_with_snack2"][0]:
            pen_lunch_size = BASE_PENALTY + meal_space["lunch_size_no_snack1_with_snack2"][0] - P["lunch_size"]
        elif P["lunch_size"] > meal_space["lunch_size_no_snack1_with_snack2"][1]:
            pen_lunch_size = BASE_PENALTY + P["lunch_size"] - meal_space["lunch_size_no_snack1_with_snack2"][1]
        else:
            pen_lunch_size = 0
    else:  # s1 > 0 and s2 >0
        if P["lunch_size"] < meal_space["lunch_size_with_snack1_and_2"][0]:
            pen_lunch_size = BASE_PENALTY + meal_space["lunch_size_with_snack1_and_2"][0] - P["lunch_size"]
        elif P["lunch_size"] > meal_space["lunch_size_with_snack1_and_2"][1]:
            pen_lunch_size = BASE_PENALTY + P["lunch_size"] - meal_space["lunch_size_with_snack1_and_2"][1]
        else:
            pen_lunch_size = 0
    return pen_lunch_size


def dinner_time(meal_space, P, s3) -> Tuple[float, float]:
    # 7-8. if there is snack 3, dinner must be between 16 and 20 and lunch and dinner must be between 4 and 6 hours apart
    #       If there is no snack 3, dinner must be between 17 and 21 and lunch and dinner must be between 5 and 7 hours apart
    if s3 > 0:
        if P["dinner_time"] - error > meal_space["dinner_time_with_snack3"][1]:
            pen_dinner_time_h = BASE_PENALTY + P["dinner_time"] - meal_space["dinner_time_with_snack3"][1]
        else:
            pen_dinner_time_h = 0

        if P["dinner_time"] + error < P["lunch_time"] + meal_space["dinner_d_with_snack3"][0]:
            pen_dinner_time_d = BASE_PENALTY + (P["lunch_time"] + meal_space["dinner_d_with_snack3"][0]) - P[
                "dinner_time"]
        elif P["dinner_time"] - error > P["lunch_time"] + meal_space["dinner_d_with_snack3"][1]:
            pen_dinner_time_d = BASE_PENALTY + P["dinner_time"] - (
                    P["lunch_time"] + meal_space["dinner_d_with_snack3"][1])
        else:
            pen_dinner_time_d = 0

    else:  # s3 == 0
        if P["dinner_time"] + error < meal_space["dinner_time_no_snack3"][0]:
            pen_dinner_time_h = BASE_PENALTY + meal_space["dinner_time_no_snack3"][0] - P["dinner_time"]
        else:
            pen_dinner_time_h = 0

        if P["dinner_time"] + error < P["lunch_time"] + meal_space["dinner_d_no_snack3"][0]:
            pen_dinner_time_d = BASE_PENALTY + (P["lunch_time"] + meal_space["dinner_d_no_snack3"][0]) - P[
                "dinner_time"]
        elif P["dinner_time"] - error > P["lunch_time"] + meal_space["dinner_d_no_snack3"][1]:
            pen_dinner_time_d = BASE_PENALTY + P["dinner_time"] - (
                        P["lunch_time"] + meal_space["dinner_d_no_snack3"][1])
        else:
            pen_dinner_time_d = 0

    return pen_dinner_time_h, pen_dinner_time_d


def dinner_size(meal_space, P, s3) -> float:
    # Dinner size and snack 3 constraint
    if s3 > 0 and P["dinner_size"] > meal_space["dinner_size_with_snack3"][1]:
        pen_dinner_size = BASE_PENALTY + P["dinner_size"] - meal_space["dinner_size_with_snack3"][1]
    elif s3 == 0 and P["dinner_size"] < meal_space["dinner_size_no_snack3"][0]:
        pen_dinner_size = BASE_PENALTY + meal_space["dinner_size_no_snack3"][0] - P["dinner_size"]
    else:
        pen_dinner_size = 0
    return pen_dinner_size


def get_penalties_names():
    return ["snacks_12_ALO",
            "breakfast_time",
            "breakfast_size",
            "lunch_time",
            "lunch_size",
            "dinner_time_h",
            "dinner_time_d",
            "dinner_size"
]