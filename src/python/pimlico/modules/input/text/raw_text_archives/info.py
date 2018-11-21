# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Input reader for raw text file collections stored in archives.
Reads archive files from arbitrary locations specified by a list of and
iterates over the files they contain.

The input paths must be absolute paths, but remember that you can make use of various
:doc:`special substitutions in the config file </core/config>` to give paths relative to your project
root, or other locations.

Unlike :mod:`~pimlico.modules.input.text.raw_text_files`, globs are not
permitted. There's no reason why they could not be, but they are not allowed
for now, to keep these modules simpler. This feature could be added, or if
you need it, you could create your own input reader module based on this
one.

All paths given are assumed to be required for the dataset to be ready,
unless they are preceded by a ``?``.

.. seealso::

   :mod:`~pimlico.modules.input.text.raw_text_files` for raw files not in archives

"""
import os
from glob import iglob

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.core.modules.options import comma_separated_strings, opt_type_help, opt_type_example
from pimlico.datatypes.corpora.data_points import RawTextDocumentType

comma_separated_paths = opt_type_help("absolute file path")(comma_separated_strings)
comma_separated_paths = opt_type_example("path1,path2,...")(comma_separated_paths)


def get_paths_from_options(input_fns, error_on_missing=False):
    """
    Iterates over paths to all the files specified in the ``files`` option.
    If ``error_on_missing=True``, non-optional paths or globs that do not
    correspond to an existing file cause an IOError to be raised.

    """
    for input_fn in input_fns:
        optional = False
        if input_fn.startswith("?"):
            # Optional path, don't error if the file doesn't exist
            optional = True
            input_fn = input_fn[1:]

        if not os.path.exists(input_fn) or not os.path.isfile(input_fn):
            if optional or not error_on_missing:
                # Skip this path, since it's optional, or we're not supposed to raise an error
                continue
            else:
                raise IOError("path '{}' does not point to a file".format(input_fn))
        else:
            yield input_fn


# TODO Continue with this
def data_ready(options):
    """
    Like get_paths_from_options, but faster (in some cases), as it just checks whether there are
    any file for each path.

    Takes module options and checks whether the dataset is ready to read.

    """
    input_fns = options["files"]
    exclude = options["exclude"] or []
    # Make sure we get at least one file, even if everything is optional
    got_something = False
    for input_fn in input_fns:
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


def corpus_len(reader):
    return sum(1 for __ in get_paths_from_options(reader.options))


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
            "help": "Comma-separated list of absolute paths to files to include in the collection. "
                    "Place a '?' at the start of a filename to indicate that it's optional",
            "type": comma_separated_paths,
            "required": True,
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
    module_type_name="raw_text_archives_reader",
    module_readable_name="Raw text archives",
)
