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
import tarfile

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.core.modules.options import comma_separated_strings, opt_type_help, opt_type_example
from pimlico.datatypes.corpora.data_points import RawTextDocumentType

comma_separated_paths = opt_type_help("absolute file path")(comma_separated_strings)
comma_separated_paths = opt_type_example("path1,path2,...")(comma_separated_paths)


def get_paths_from_options(options, error_on_missing=False):
    """
    Iterates over paths to all the files specified in the ``files`` option.
    If ``error_on_missing=True``, non-optional paths or globs that do not
    correspond to an existing file cause an IOError to be raised.

    """
    for input_fn in options["files"]:
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


def iter_archive(path):
    """
    Iterate over the documents in a tar archive

    :param path: path to archive

    """
    with tarfile.open(path, "r") as archive:
        for tarinfo in archive:
            if tarinfo.isfile():
                yield tarinfo.name, archive.extractfile(tarinfo).read()
            archive.members = []


def _iter_archive_infos(path):
    """
    Iterate over the documents in a tar archive without reading them:
    just for counting.

    :param path: path to archive

    """
    with tarfile.open(path, "r") as archive:
        for tarinfo in archive:
            if tarinfo.isfile():
                yield tarinfo
            archive.members = []


def data_ready(options):
    """
    Like get_paths_from_options, but faster (in some cases), as it just checks whether there are
    any file for each path.

    Takes module options and checks whether the dataset is ready to read.

    """
    # Make sure we get at least one file, even if everything is optional
    got_something = False
    try:
        # Try looping over the files: if a non-optional one is missing, this will raise an error
        for path in get_paths_from_options(options, error_on_missing=True):
            # Check that there's at least one document in the archive
            try:
                next(iter_archive(path))
            except StopIteration:
                # Empty archive: don't count this towards having some input
                pass
            else:
                got_something = True
    except IOError:
        return False
    return got_something


def corpus_len(options):
    """ Just count up the documents without reading them. """
    return sum(1 for path in get_paths_from_options(options) for __ in _iter_archive_infos(path))


def corpus_iter(reader):
    options = reader.options
    encoding = options["encoding"]
    encoding_errors = options["encoding_errors"]

    used_archive_names = set()
    paths = list(get_paths_from_options(options))
    for path in paths:
        used_doc_names = set()

        # Use the file basenames as doc names where possible, but make sure they're unique
        base_archive_name = os.path.splitext(os.path.basename(path))[0]
        archive_name = base_archive_name
        distinguish_id = 0
        # Keep increasing the distinguishing ID until we have a unique name
        while archive_name in used_archive_names:
            archive_name = "%s-%d" % (base_archive_name, distinguish_id)
            distinguish_id += 1
        used_archive_names.add(archive_name)

        for member_name, data in iter_archive(path):
            # Decode to unicode string, which will be used as data for document
            data = data.decode(encoding, errors=encoding_errors)
            # Get a unique doc name within the archive
            base_doc_name = os.path.splitext(member_name)[0]
            doc_name = base_doc_name
            # Keep increasing the distinguishing ID until we have a unique name
            while doc_name in used_doc_names:
                doc_name = "%s-%d" % (base_doc_name, distinguish_id)
                distinguish_id += 1
            used_doc_names.add(doc_name)

            # If there's only one archive, don't include the archive name in the doc name
            if len(paths) > 1:
                doc_name = "{}/{}".format(archive_name, doc_name)

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
    # Make the module executable to count the docs, since this can take a while
    # with large tar archives
    execute_count=True,
)
