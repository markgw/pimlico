"""
Command-line tools for manipulating Pimarcs.

"""
import argparse
import os

from pimlico.utils.pimarc import PimarcReader


def list_files(opts):
    path = opts.path
    reader = PimarcReader(path)
    for filename in reader.iter_filenames():
        print(filename)


def extract_file(opts):
    if opts.out is None:
        out_path = os.getcwd()
    else:
        out_path = os.path.abspath(opts.out)

    path = opts.path
    filenames = opts.filenames

    reader = PimarcReader(path)
    for filename in filenames:
        print("Extracting {}".format(filename))
        metadata, data = reader[filename]
        with open(os.path.join(out_path, filename), "wb") as f:
            f.write(data)


def no_subcommand(opts):
    print("Specify a subcommand: list, ...")


def run():
    parser = argparse.ArgumentParser("pimlico.utils.pimarc")
    parser.set_defaults(func=no_subcommand)
    subparsers = parser.add_subparsers(help="Select a sub-command")

    subparser = subparsers.add_parser("list", help="List files in a Pimarc")
    subparser.set_defaults(func=list_files)
    subparser.add_argument("path", help="Path to the Pimarc")

    subparser = subparsers.add_parser("extract", help="Extract a file from a Pimarc")
    subparser.set_defaults(func=extract_file)
    subparser.add_argument("path", help="Path to the Pimarc")
    subparser.add_argument("filenames", nargs="+", help="Filename(s) to extract")
    subparser.add_argument("--out", "-o", help="Output dir (default CWD)")

    opts = parser.parse_args()
    opts.func(opts)


if __name__ == "__main__":
    # Command-line utilities for manipulating Pimarcs
    run()
