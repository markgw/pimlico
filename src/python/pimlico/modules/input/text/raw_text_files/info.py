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

.. seealso::

   Datatype :class:`pimlico.datatypes.files.UnnamedFileCollection`
      The datatype previously used for reading in file collections, now being phased out to be replaced
      by this input reader.

"""
import fnmatch
import os
from glob import glob, iglob

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.core.modules.options import comma_separated_strings, comma_separated_list, opt_type_help
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


@opt_type_help("(line range-limited) file path")
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


def get_paths_from_options(options, error_on_missing=False):
    """
    Get a list of paths to all the files specified in the ``files`` option. If ``error_on_missing=True``,
    non-optional paths or globs that do not correspond to an existing file cause an IOError to be raised.

    """
    input_fns = options["files"]
    paths = []
    for input_fn, s, e in input_fns:
        optional = False
        if input_fn.startswith("?"):
            # Optional path, don't error if the file doesn't exist
            optional = True
            input_fn = input_fn[1:]
        # Interpret the path as a glob
        # If it's not a glob, it will just give us one path
        matching_paths = glob(input_fn)
        # Only interested in files, not directories
        matching_paths = [p for p in matching_paths if os.path.isfile(p)]
        # Sort matching paths alphabetically, to be sure that they're always in the same order
        matching_paths.sort()
        # If no paths match, either the path was a glob that didn't match anything or a non-existent file
        if len(matching_paths) == 0 and not optional and error_on_missing:
            raise IOError("path '%s' does not exist, or is a glob that matches nothing" % input_fn)
        paths.extend([(p, s, e) for p in matching_paths])

    if options["exclude"] is not None:
        for excl_path in options["exclude"]:
            # Treat this as a glob too
            excl_matching_paths = glob(excl_path)
            paths = [(p, s, e) for (p, s, e) in paths if p not in excl_matching_paths]
    return paths


def check_paths_from_options(options):
    """
    Like get_paths_from_options, but faster (in some cases), as it just checks whether there are
    any file for each path/glob.

    """
    input_fns = options["files"]
    exclude = options["exclude"] or []
    # Make sure we get at least one file, even if everything is optional
    got_something = False
    for input_fn, s, e in input_fns:
        if input_fn.startswith("?"):
            # Optional path, no need to check this
            continue
        # Interpret the path as a glob
        # If it's not a glob, it will just give us one path
        matching_paths = iglob(input_fn)
        # Only interested in files, not directories
        glob_matched = False
        for path in matching_paths:
            if os.path.isfile(path):
                # Check this doesn't match an exclude pattern
                if not any(fnmatch.fnmatch(path, excl_path) for excl_path in exclude):
                    # Existing path, now we've got at least something
                    got_something = True
                    # At least one thing matched this glob: don't carry on checking
                    glob_matched = True
                    break
        if not glob_matched:
            # The glob matched no actual files: these paths are not satisfied, give up now
            return False
    return got_something


def data_ready(options):
    return check_paths_from_options(options)


def corpus_len(reader):
    if "length" in reader.metadata:
        # If the length has been stored, use that
        return reader.metadata["length"]
    else:
        return len(get_paths_from_options(reader.options))


def corpus_iter(reader):
    options = reader.options

    encoding = options["encoding"]
    # Use the file basenames as doc names where possible, but make sure they're unique
    used_doc_names = set()
    paths = get_paths_from_options(options)
    if len(paths):
        for path, start, end in paths:
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
                # Normalize encoding, but keep the data as utf8
                if not type(data) is unicode and encoding.lower() not in ["utf-8", "utf8"]:
                    data = data.decode(encoding, errors=options["encoding_errors"])
                    data = data.encode("utf8")

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

                yield doc_name, reader.datatype.data_point_type(data)


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
