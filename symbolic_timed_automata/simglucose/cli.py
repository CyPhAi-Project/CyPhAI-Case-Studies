import argparse


def get_command_line_arguments():
    parser = argparse.ArgumentParser(description="Process input")

    parser.add_argument('--seed', type=int,
                        dest='master_seed',
                        default=104,
                        help="The master random seed. The default value is 104",
                        required=False)

    parser.add_argument('-p', '--patient', '--patient-name', type=int,
                        dest='patient_name',
                        default=10,
                        help="The index of the patient. The default value is 10.",
                        required=False)

    parser.add_argument('-H', '--horizon', type=int,
                        dest='horizon',
                        default=1440,
                        help="The simulation horizon, in minutes. The default value is 1440.",
                        required=False)

    parser.add_argument('-d', '--dist-factor',  type=float,
                        dest='dist_factor',
                        help="Reduction factor for the range of meal glucose. The default value is 3.",
                        default=3.0,
                        required=False)

    parser.add_argument('-i', '--max-opt-iters', type=int,
                        dest='max_opt_iters',
                        default=100,
                        help="The maximum number of optimization iterations. The default value is 100.",
                        required=False)

    parser.add_argument('-r', '--repetitions', type=int,
                        dest='repetitions',
                        default=10,
                        help="The number of repetitions of the experiment. The default value is 10.",
                        required=False)


    parser.add_argument('-o', '--dump', type=str, dest='output',
                        help="Output path of the dump file, a json file", default=None,
                        required=False)

    parser.add_argument('-b', '--batch-size', type=int,
                        dest='batch_size',
                        default=100,
                        help="The batch size for simulating many random meal plans. The default value is 100.",
                        required=False)

    parser.add_argument('--initial-feasible', type=bool,
                        dest='initial_feasible',
                        default=True,
                        help="If the initial point of the optimization must be already feasible. The default value is True.",
                        required=False)

    return parser.parse_args()
