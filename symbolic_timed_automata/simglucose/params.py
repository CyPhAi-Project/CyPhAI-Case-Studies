
NUM_MEALS = 6


def get_whole_space(dist_factor: float):
    return {
        "breakfast_time": (5, 9),
        "breakfast_size": (40 - (dist_factor * 10), 55 + (dist_factor * 10)),

        "snack1_time": (9, 11),
        "snack1_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),

        "lunch_time": (12, 15),
        "lunch_size": (65 - (dist_factor * 10), 80 + (dist_factor * 10)),

        "snack2_time": (14, 16),
        "snack2_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),

        "dinner_time": (16, 21),
        "dinner_size": (70 - (dist_factor * 10), 85 + (dist_factor * 10)),

        "snack3_time": (20, 23),
        "snack3_size": (max(0.0, (10 - (dist_factor * 5))), 10 + (dist_factor * 5)),
    }


def get_meal_space(dist_factor: float):
    # Meal times and sizes defined for RandomScenario in simglucose
    # Bound on meal size is (mu-3*sigma, mu+3*sigma)
    # amount_mu = [45, 10, 70, 10, 80, 10]
    #         amount_sigma = [10, 5, 10, 5, 10, 5]
    return {

        "breakfast_time_with_snack1": (5, 8),
        "breakfast_size_with_snack1": (40-(dist_factor*10), 40+(dist_factor*10)),

        "breakfast_time_no_snack1": (6, 9),
        "breakfast_size_no_snack1": (55-(dist_factor*10), 55+(dist_factor*10)),


        "snack1_time": (9, 11),
        "snack1_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "lunch_time": (12, 15),
        "lunch_size_with_snack1_no_snack2": (80-(dist_factor*10), 80+(dist_factor*10)),
        "lunch_size_with_snack1_and_2": (65-(dist_factor*10), 65+(dist_factor*10)),
        "lunch_size_no_snack1_with_snack2": (70-(dist_factor*10), 70+(dist_factor*10)),

        "snack2_time": (14, 16),
        "snack2_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "dinner_time_with_snack3": (16, 20),
        "dinner_size_with_snack3": (70-(dist_factor*10), 70+(dist_factor*10)),

        "dinner_time_no_snack3": (17, 21),
        "dinner_size_no_snack3": (85-(dist_factor*10), 85+(dist_factor*10)),

        "snack3_time": (20, 23),
        "snack3_size": (max(5.0, (10-(dist_factor*5))), 10+(dist_factor*5)),

        "lunch_d_with_snack1": (4, 7),
        "lunch_d_no_snack1": (3, 6),

        "dinner_d_no_snack3": (5, 7),
        "dinner_d_with_snack3": (4, 6)
    }


'''{

        "breakfast_time_with_snack1": (5, 8),
        "breakfast_size_with_snack1": (40-(3*10)*dist_factor, 40+(3*10)*dist_factor),

        "breakfast_time_no_snack1": (6, 9),
        "breakfast_size_no_snack1": (55-(3*10)*dist_factor, 55+(3*10)*dist_factor),


        "snack1_time": (9, 11),
        "snack1_size": (max(5.0, (10-(3*5)*dist_factor)), 10+(3*5)*dist_factor),

        "lunch_time": (12, 15),
        #"lunch_size": (70-(3*10)*dist_factor, 70+(3*10)*dist_factor),
        "lunch_size_with_snack1_no_snack2": (80-(3*10)*dist_factor, 80+(3*10)*dist_factor),
        "lunch_size_with_snack1_and_2": (65-(3*10)*dist_factor, 65+(3*10)*dist_factor),
        "lunch_size_no_snack1_with_snack2": (70-(3*10)*dist_factor, 70+(3*10)*dist_factor),

        "snack2_time": (14, 16),
        "snack2_size": (max(5.0, (10-(3*5)*dist_factor)), 10+(3*5)*dist_factor),
        # "snack2_size": (10-(3*5)*DIST_FACTOR, 10+(3*5)*DIST_FACTOR),

        "dinner_time_with_snack3": (16, 20),
        "dinner_size_with_snack3": (70-(3*10)*dist_factor, 70+(3*10)*dist_factor),

        "dinner_time_no_snack3": (17, 21),
        "dinner_size_no_snack3": (85-(3*10)*dist_factor, 85+(3*10)*dist_factor),

        "snack3_time": (20, 23),
        "snack3_size": (max(5.0, (10-(3*5)*dist_factor)), 10+(3*5)*dist_factor),

        "lunch_d_with_snack1": (4, 7),
        "lunch_d_no_snack1": (3, 6),

        "dinner_d_no_snack3": (5, 7),
        "dinner_d_with_snack3": (4, 6)
    }'''
