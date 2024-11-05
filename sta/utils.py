import argparse

def get_command_line_arguments():
    parser = argparse.ArgumentParser(description="Syma + Wordgen constrainted trajectory generation")

    parser.add_argument('-n', '--number', type=int,
                        help="The number of trajectories to generate",
                        required=True)

    parser.add_argument('-l', '--length', type=int,
                        help="The length of trajectories in terms of number of events",
                        required=True)

    parser.add_argument('-o', '--dump', '--output', '--output-pattern', type=str, dest='output_pattern',
                        help="Pattern (path) of .mat files to store the generated trajectories, using Python's pattern format",
                        required=True)

    parser.add_argument('-c', '--concrete', '--concrete-out', type=str, dest='concrete',
                        help="Output path of the generated concrete trajectories, a json file", default=None,
                        required=True)

    parser.add_argument('-a', '--abstract', '--abstract-out', type=str, dest='abstract',
                        help="Output path of the generated abstract trajectories, a json file",
                        required=True)

    parser.add_argument('-s', '--sta', '--sta-out', type=str, dest='sta_out_filename',
                        help="Output path of the generated STA, in PRISM format",
                        required=True)

    parser.add_argument('-d', '--dt', type=float,
                        help="The time step for generated trajectories", default=0.001,
                        required=False)

    parser.add_argument('-w', '--wg', '--wordgen', '--wordgen-path',
                        type=str, dest="wordgen_path",
                        help="Path of Wordgen executable. If not specified, it is assumed to be in the PATH",
                        default="Wordgen", required=False)

    args = parser.parse_args()
    return args
