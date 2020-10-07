# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Command-line tools for manipulating Pimarcs.

"""
import argparse
import os
import shutil
from tarfile import TarFile

import sys

from pimlico.utils.pimarc import PimarcReader, PimarcWriter
from pimlico.utils.pimarc.index import check_index, IndexCheckFailed
from .index import reindex


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

    with PimarcReader(path) as reader:
        for filename in filenames:
            print("Extracting {}".format(filename))
            metadata, data = reader[filename]
            with open(os.path.join(out_path, filename), "wb") as f:
                f.write(data)


def append_file(opts):
    path = os.path.abspath(opts.path)
    if not path.endswith(".prc"):
        print("Pimarc data file must use extension '.prc'")
    paths_to_add = opts.files
    # Append if the file already exists, otherwise create a new archive
    append = os.path.exists(path)
    if append:
        print("Appending files to existing pimarc {}".format(path))
    else:
        print("Creating new pimarc {}".format(path))

    with PimarcWriter(path, mode="a" if append else "w") as writer:
        # First check that all files can be added
        for path_to_add in paths_to_add:
            path_to_add = os.path.abspath(path_to_add)
            if not os.path.exists(path_to_add):
                print("Cannot add {}: file does not exist".format(path_to_add))
                sys.exit(1)
            filename = os.path.basename(path_to_add)
            if filename in writer.index:
                print("Cannot add {}: filename '{}' already exists in archive".format(path_to_add, filename))
                sys.exit(1)

        # Now add the files
        for path_to_add in paths_to_add:
            path_to_add = os.path.abspath(path_to_add)
            # Just use the basename when adding the file: no paths are stored in pimarcs
            filename = os.path.basename(path_to_add)
            print("  Adding {} as {}".format(path_to_add, filename))
            # Read in the file's data
            with open(path_to_add, "rb") as f:
                data = f.read()
            writer.write_file(data, filename)


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


def reindex_pimarcs(opts):
    if not all(path.endswith(".prc") for path in opts.paths):
        print("Pimarc files must have correct extension: .prc")
        sys.exit(1)

    for pimarc_path in opts.paths:
        print("Rebuilding index for {}".format(pimarc_path))
        reindex(pimarc_path)
        print("  Success")


def check_pimarcs(opts):
    if not all(path.endswith(".prc") for path in opts.paths):
        print("Pimarc files must have correct extension: .prc")
        sys.exit(1)

    total_length = 0
    for pimarc_path in opts.paths:
        print("Checking index for {}".format(pimarc_path))
        try:
            length = check_index(pimarc_path)
            print("  Success ({:,d} members)".format(length))
            total_length += length
        except IndexCheckFailed as e:
            print("  {}".format(e))

    print("Total members in all archives: {:,d}".format(total_length))


def remove(opts):
    path = os.path.abspath(opts.path)
    if not path.endswith(".prc"):
        print("Pimarc data file must use extension '.prc'")

    files_to_remove = opts.files
    remove_all_after = opts.after
    remove_after_found = False

    if len(files_to_remove) == 0 and remove_all_after is None:
        print("No files to remove")
        sys.exit(0)

    # Write to a temporary new archive
    tmp_arc = "{}.tmp".format(path)
    try:
        with PimarcWriter(tmp_arc, mode="w") as writer:
            with PimarcReader(path) as reader:
                for metadata, data in reader:
                    name = metadata["name"]
                    if name in files_to_remove:
                        files_to_remove.remove(name)
                        print("Removing {}".format(name))
                    else:
                        # Pass the file straight through
                        writer.write_file(data, metadata=metadata)

                    if remove_all_after == name:
                        # Written this file, now stop
                        print("Stopping after {}".format(name))
                        remove_after_found = True
                        break

        if remove_all_after is not None and not remove_after_found:
            print("ERROR: filename {} not found in archive".format(remove_all_after))
            return
        if len(files_to_remove) > 0:
            print("ERROR: some files not found in archive: {}".format(", ".join(files_to_remove)))
            return

        # Replace the old archive with the new one
        print("Writing new archive to {}".format(path))
        os.replace(tmp_arc, path)
        os.replace("{}i".format(tmp_arc), "{}i".format(path))
    finally:
        # Remove the temporary archive
        if os.path.exists(tmp_arc):
            os.remove(tmp_arc)
        if os.path.exists("{}i".format(tmp_arc)):
            os.remove("{}i".format(tmp_arc))


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

    subparser = subparsers.add_parser("append", help="Append a file to a pimarc. "
                                                     "If the pimarc doesn't exist, it is created")
    subparser.set_defaults(func=append_file)
    subparser.add_argument("path", help="Path to the pimarc (.prc file)")
    subparser.add_argument("files", nargs="+", help="Path(s) to add")

    subparser = subparsers.add_parser("fromtar",
                                      help="Create a Pimarc containing all the same files as a given tar. "
                                           "Outputs to the same filename as input, with '.tar' replaced by '.prc'")
    subparser.set_defaults(func=from_tar)
    subparser.add_argument("tars", nargs="+", help="Path to the tar archive(s)")
    subparser.add_argument("--out-path", "-o", help="Directory to output files to. Defaults to same as input")
    subparser.add_argument("--delete", "-d", action="store_true", help="Delete the tar files after creating pimarcs")

    subparser = subparsers.add_parser("reindex",
                                      help="Rebuild a pimarc's index (the .prci file) from its data (the .prc file). "
                                           "This can be necessary if the index has become corrupted or something when "
                                           "wrong during writing of the archive")
    subparser.set_defaults(func=reindex_pimarcs)
    subparser.add_argument("paths", nargs="+", help="Path to the pimarc(s) - .prc files")

    subparser = subparsers.add_parser("check",
                                      help="Check a pimarc's index (the .prci file) against its data (the .prc file). "
                                           "This can be useful for debugging writing code, or checking whether the "
                                           "index should be rebuilt")
    subparser.set_defaults(func=check_pimarcs)
    subparser.add_argument("paths", nargs="+", help="Path to the pimarc(s) - .prc files")

    subparser = subparsers.add_parser("remove",
                                      help="Remove files from a Pimarc archive")
    subparser.set_defaults(func=remove)
    subparser.add_argument("path", help="Path to the pimarc - .prc file")
    subparser.add_argument("files", nargs="*", help="Names of files to remove")
    subparser.add_argument("--after", action="store", help="Remove all files after the given name")

    opts = parser.parse_args()
    opts.func(opts)


if __name__ == "__main__":
    # Command-line utilities for manipulating Pimarcs
    run()
