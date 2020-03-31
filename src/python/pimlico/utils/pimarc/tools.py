"""
Command-line tools for manipulating Pimarcs.

"""
import argparse
import os
from tarfile import TarFile

from pimlico.utils.pimarc import PimarcReader, PimarcWriter


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


def from_tar(opts):
    in_tar_paths = opts.tars
    out_dir_path = opts.out_path

    for tar_path in in_tar_paths:
        tar_path = os.path.abspath(tar_path)

        # Work out where to put the converted file
        out_filename = "{}.prc".format(os.path.splitext(os.path.basename(tar_path))[0])
        if out_dir_path is None:
            out_path = os.path.join(os.path.dirname(tar_path), out_filename)
        else:
            out_path = os.path.join(out_dir_path, out_filename)
        print("Creating {} from {}".format(out_path, tar_path))

        # Create a writer to add files to
        with PimarcWriter(out_path) as arc:
            # Read in the tar file
            tarfile = TarFile.open(tar_path, "r:")
            for tarinfo in tarfile:
                name = tarinfo.name
                with tarfile.extractfile(tarinfo) as tar_member:
                    data = tar_member.read()
                print("  Writing {}".format(name))
                arc.write_file(data, name)

        if opts.delete:
            print("Deleting tar: {}".format(tar_path))
            os.remove(tar_path)


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

    subparser = subparsers.add_parser("fromtar",
                                      help="Create a Pimarc containing all the same files as a given tar. "
                                           "Outputs to the same filename as input, with '.tar' replaced by '.prc'")
    subparser.set_defaults(func=from_tar)
    subparser.add_argument("tars", nargs="+", help="Path to the tar archive(s)")
    subparser.add_argument("--out-path", "-o", help="Directory to output files to. Defaults to same as input")
    subparser.add_argument("--delete", "-d", action="store_true", help="Delete the tar files after creating pimarcs")

    opts = parser.parse_args()
    opts.func(opts)


if __name__ == "__main__":
    # Command-line utilities for manipulating Pimarcs
    run()
