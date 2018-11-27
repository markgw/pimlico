# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Input reader for raw text file collections. Reads in files from arbitrary locations specified by a
list of globs.

The input paths must be absolute paths (or globs), but remember that you can make use of various
:doc:`special substitutions in the config file </core/config>` to give paths relative to your project
root, or other locations.

The file paths may use `globs <https://docs.python.org/2/library/glob.html>`_ to match multiple files.
By default, it is assumed that every filename should exist and every glob should match at least one
file. If this does not hold, the dataset is assumed to be not ready. You can override this by placing
a ``?`` at the start of a filename/glob, indicating that it will be included if it exists, but is
not depended on for considering the data ready to use.

"""
import fnmatch
import os
from glob import glob, iglob

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.core.modules.options import comma_separated_strings, comma_separated_list, opt_type_help, opt_type_example
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


@opt_type_help("(line range-limited) file path")
@opt_type_example("path")
def filename_with_range(val):
    """ Option processor for file paths with an optional start and end line at the end. """
    if ":" in val:
        path, __, range = val.rpartition(":")
        if "-" not in range:
            raise ValueError("invalid line range specifier '%s' in file path" % range)
        start, __, end = range.partition("-")
        if len(start) == 0:
            start = 0
        if len(end) == 0:
            end = -1

        try:
            start = int(start)
            end = int(end)
        except ValueError:
            raise ValueError("invalid line range specifier '%s' in file path" % range)
        return path, start, end
    else:
        return val, 0, -1


comma_separated_paths = comma_separated_list(filename_with_range)
comma_separated_paths = opt_type_example("path1,path2,...")(comma_separated_paths)


def to_exclude_path(path, exclude_pattern):
    # Check if the path matches the pattern as a glob
    if fnmatch.fnmatch(path, exclude_pattern):
        return True
    # Otherwise, if it's not an abs path, check whether it matches as a suffix
    if not os.path.isabs(exclude_pattern) and path.endswith(exclude_pattern) and \
        (len(path) == len(exclude_pattern) or path[-(len(exclude_pattern)+1)] == os.path.sep):
        return True
    return False


def _get_paths_from_options_without_exclude(input_fns, error_on_missing=False):
    """
    Iterates over paths to all the files specified in the ``files`` option.
    If ``error_on_missing=True``, non-optional paths or globs that do not
    correspond to an existing file cause an IOError to be raised.

    Doesn't apply excludes.

    """
    for input_fn, start, end in input_fns:
        optional = False
        if input_fn.startswith("?"):
            # Optional path, don't error if the file doesn't exist
            optional = True
            input_fn = input_fn[1:]
        # Before checking whether it's a glob, check if it's a directory
        if os.path.isdir(input_fn):
            got_file = False
            for doc_name, file_path in get_paths_from_directory(input_fn):
                if not got_file:
                    got_file = True
                yield doc_name, file_path, start, end
            if error_on_missing and not got_file:
                raise IOError("path '{}' is a directory, but it doesn't contain any files".format(input_fn))
        else:
            # Interpret the path as a glob
            # If it's not a glob, it will just give us one path
            matching_paths = glob(input_fn)
            # Only interested in files now, not directories
            matching_paths = [p for p in matching_paths if os.path.isfile(p)]
            # Sort matching paths alphabetically, to be sure that they're always in the same order
            matching_paths.sort()
            # If no paths match, either the path was a glob that didn't match anything or a non-existent file
            if len(matching_paths) == 0 and not optional and error_on_missing:
                raise IOError("path '%s' does not exist, or is a glob that matches nothing" % input_fn)
            for path in matching_paths:
                yield None, path, start, end


def get_paths_from_directory(path):
    for root, dirs, files in os.walk(path):
        for filename in files:
            # Get a doc name as the relative path within the dir
            doc_name = os.path.relpath(os.path.join(root, filename), path)
            yield doc_name, os.path.join(path, root, filename)


def get_paths_from_options(options, error_on_missing=False):
    """
    Iterates over paths to all the files specified in the ``files`` option.
    If ``error_on_missing=True``, non-optional paths or globs that do not
    correspond to an existing file cause an IOError to be raised.

    """
    input_fns = options["files"]
    if options["exclude"] is not None:
        excl_paths = options["exclude"]
    else:
        excl_paths = []

    for doc_name, path, start, end in _get_paths_from_options_without_exclude(input_fns, error_on_missing=error_on_missing):
        if not any(to_exclude_path(path, excl_path) for excl_path in excl_paths):
            yield doc_name, path, start, end


def data_ready(options):
    """
    Like get_paths_from_options, but faster (in some cases), as it just checks whether there are
    any file for each path/glob.

    Takes module options and checks whether the dataset is ready to read.

    """
    input_fns = options["files"]
    exclude = options["exclude"] or []
    # Make sure we get at least one file, even if everything is optional
    got_something = False
    for input_fn, start, end in input_fns:
        if input_fn.startswith("?"):
            # Optional path, no need to check this
            continue
        # Before checking whether it's a glob, check if it's a directory
        if os.path.isdir(input_fn):
            # Don't need to get all the filenames, just check whether there's one
            try:
                next(get_paths_from_directory(input_fn))
            except StopIteration:
                # Directory given, but no files in there
                return False
            got_something = True
        else:
            # Interpret the path as a glob
            # If it's not a glob, it will just give us one path
            matching_paths = iglob(input_fn)
            # Only interested in files, not directories
            glob_matched = False
            for path in matching_paths:
                if os.path.isfile(path):
                    # Check this doesn't match an exclude pattern
                    if not any(to_exclude_path(path, excl_path) for excl_path in exclude):
                        # Existing path, now we've got at least something
                        got_something = True
                        # At least one thing matched this glob: don't carry on checking
                        glob_matched = True
                        break

            if not glob_matched:
                # The glob matched no actual files: these paths are not satisfied, give up now
                return False
    return got_something


def corpus_len(options):
    return sum(1 for __ in get_paths_from_options(options))


def corpus_iter(reader):
    options = reader.options

    encoding = options["encoding"]
    # Use the file basenames as doc names where possible, but make sure they're unique
    used_doc_names = set()
    for doc_name, path, start, end in get_paths_from_options(options):
        if doc_name is None:
            doc_name = os.path.basename(path)
            distinguish_id = 0
            # Keep increasing the distinguishing ID until we have a unique name
            while doc_name in used_doc_names:
                base, ext = os.path.splitext(doc_name)
                doc_name = "%s-%d%s" % (base, distinguish_id, ext)
                distinguish_id += 1
            used_doc_names.add(doc_name)

        with open(path, "r") as f:
            data = f.read()
            # Decode to unicode string, which will be used as data for document
            data = data.decode(encoding, errors=options["encoding_errors"])

            if start != 0 or end != -1:
                # start=0 (i.e. no cutting) is the same as start=1 (start from first line)
                if start != 0:
                    # Otherwise, shift down to account for 1-indexing
                    start -= 1
                if end != -1:
                    end -= 1

                lines = data.split("\n")
                if end == -1:
                    data = u"\n".join(lines[start:])
                else:
                    data = u"\n".join(lines[start:end+1])

            yield doc_name, reader.datatype.data_point_type(text=data)


ModuleInfo = iterable_input_reader(
    {
        "files": {
            "help": "Comma-separated list of absolute paths to files to include in the collection. Paths may include "
                    "globs. Place a '?' at the start of a filename to indicate that it's optional. You can specify "
                    "a line range for the file by adding ':X-Y' to the end of the path, where X is the first line "
                    "and Y the last to be included. Either X or Y may be left empty. (Line numbers are 1-indexed.)",
            "type": comma_separated_paths,
            "required": True,
        },
        "exclude": {
            "help": "A list of files to exclude. Specified in the same way as `files` (except without line ranges). "
                    "This allows you to specify a glob in `files` and then exclude individual files from it (you "
                    "can use globs here too)",
            "type": comma_separated_strings,
        },
        "encoding": {
            "help": "Encoding to assume for input files. Default: utf8",
            "default": "utf8",
        },
        "encoding_errors": {
            "help": "What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 "
                    "chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details",
            "default": "strict",
        },
    },
    RawTextDocumentType(),
    data_ready, corpus_len, corpus_iter,
    module_type_name="raw_text_files_reader",
    module_readable_name="Raw text files",
)
