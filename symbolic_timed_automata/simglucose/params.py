
NUM_MEALS = 6


def get_whole_space(dist_factor: float):
    return {
        "breakfast_time": (5, 9),
        "breakfast_size": (40 - (dist_factor * 10), 55 + (dist_factor * 10)),

        "snack_1_time": (9, 11),
        "snack_1_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),

        "lunch_time": (12, 15),
        "lunch_size": (65 - (dist_factor * 10), 80 + (dist_factor * 10)),

        "snack_2_time": (14, 16),
        "snack_2_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),

        "dinner_time": (16, 21),
        "dinner_size": (70 - (dist_factor * 10), 85 + (dist_factor * 10)),

        "snack_3_time": (20, 23),
        "snack_3_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),
    }


def get_meal_space(dist_factor: float):
    # Meal times and sizes defined for RandomScenario in simglucose
    # Bound on meal size is (mu-3*sigma, mu+3*sigma)
    # amount_mu = [45, 10, 70, 10, 80, 10]
    #         amount_sigma = [10, 5, 10, 5, 10, 5]
    return {

        "breakfast_time_with_snack_1": (5, 6),
        "breakfast_size_with_snack_1": (40-(dist_factor*10), 40+(dist_factor*10)),

        "breakfast_time_no_snack_1": (6, 9),
        "breakfast_size_no_snack_1": (55-(dist_factor*10), 55+(dist_factor*10)),


        "snack_1_time": (9, 11),
        "snack_1_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "lunch_time_with_snack_1_and_2": (12, 13),
        "lunch_time_no_snack_1": (12, 13),
        "lunch_time_no_snack_2": (12, 15),
        "lunch_size_no_snack_2": (80-(dist_factor*10), 80+(dist_factor*10)),
        "lunch_size_with_snack_1_and_2": (65-(dist_factor*10), 65+(dist_factor*10)),
        "lunch_size_no_snack_1": (70-(dist_factor*10), 70+(dist_factor*10)),

        "snack_2_time": (14, 16),
        "snack_2_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "dinner_time_with_snack_3": (16, 17),
        "dinner_size_with_snack_3": (70-(dist_factor*10), 70+(dist_factor*10)),

        "dinner_time_no_snack_3": (17, 21),
        "dinner_size_no_snack_3": (85-(dist_factor*10), 85+(dist_factor*10)),

        "snack_3_time": (20, 23),
        "snack_3_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "lunch_d_with_snack_1_and_2": (6, 7),
        "lunch_d_no_snack_1": (3, 6),
        "lunch_d_no_snack_2": (4, 7),

        "dinner_d_with_snack_3": (4, 6),
        "dinner_d_no_snack_3": (5, 7),
    }
