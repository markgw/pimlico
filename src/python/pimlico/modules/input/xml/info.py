# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Input reader for XML file collections.  Gigaword, for example, is stored in this way.
The data retrieved from the files is plain unicode text.

.. todo::

   Add test pipeline

"""

import fnmatch
import io
import os
from glob import iglob, glob
from gzip import GzipFile

from pimlico.core.dependencies.python import beautiful_soup_dependency, safe_import_bs4
from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.core.modules.options import comma_separated_strings, opt_type_help
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


def get_paths_from_options(options, error_on_missing=False):
    """
    Get a list of paths to all the files specified in the ``files`` option. If ``error_on_missing=True``,
    non-optional paths or globs that do not correspond to an existing file cause an IOError to be raised.

    """
    input_fns = options["files"]
    paths = []
    for input_fn in input_fns:
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
        paths.extend([p for p in matching_paths])

    if options["exclude"] is not None:
        for excl_path in options["exclude"]:
            # Treat this as a glob too
            excl_matching_paths = glob(excl_path)
            paths = [(p, s, e) for (p, s, e) in paths if p not in excl_matching_paths]
    return paths


def data_ready(options):
    """
    Like get_paths_from_options, but faster (in some cases), as it just checks whether there are
    any file for each path/glob.

    """
    input_fns = options["files"]
    exclude = options["exclude"] or []
    # Make sure we get at least one file, even if everything is optional
    got_something = False
    for input_fn in input_fns:
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


def get_doc_nodes(filename, document_node_type, encoding, attr_constraints=None):
    if attr_constraints is None:
        attr_constraints = {}
    safe_import_bs4()
    from bs4 import BeautifulSoup

    if filename.endswith(".gz"):
        # Permit gzip files by opening them using the gzip library
        with GzipFile(filename, fileobj=open(filename, mode="rb")) as f:
            data = f.read()
            data = data.decode(encoding)
    else:
        with io.open(filename, mode="r", encoding=encoding) as f:
            data = f.read()

    # Read the XML using Beautiful Soup, so we can handle messy XML in a tolerant fashion
    # We specify XML, instead of HTML
    soup = BeautifulSoup(data, "xml")
    # Look for the type of XML node that documents are stored in and count them
    return soup.find_all(document_node_type, attrs=attr_constraints)


def corpus_len(options):
    """ Faster iteration over doc nodes, just to count up how many there are """
    encoding = options["encoding"]
    # Special case: use filename as doc name
    doc_node_type = options["document_node_type"]
    attr_constraints = options["filter_on_doc_attr"]

    # Use the file basenames as doc names where possible, but make sure they're unique
    paths = get_paths_from_options(options)
    count = 0
    if len(paths):
        for path in paths:
            count += len(list(get_doc_nodes(path, doc_node_type, encoding, attr_constraints)))
    return count


def iter_files(reader):
    options = reader.options

    encoding = options["encoding"]
    doc_name_attr = options["document_name_attr"]
    # Special case: use filename as doc name
    doc_name_from_fn = doc_name_attr == "filename"
    doc_node_type = options["document_node_type"]
    attr_constraints = options["filter_on_doc_attr"]

    # Use the file basenames as doc names where possible, but make sure they're unique
    used_doc_names = set()
    paths = get_paths_from_options(options)
    if len(paths):
        for path in paths:
            if doc_name_from_fn:
                base_doc_name = os.path.basename(path)
                distinguish_id = 0
                # Keep increasing the distinguishing ID until we have a unique name
                while base_doc_name in used_doc_names:
                    base, ext = os.path.splitext(base_doc_name)
                    base_doc_name = "%s-%d%s" % (base, distinguish_id, ext)
                    distinguish_id += 1
                used_doc_names.add(base_doc_name)

            for file_doc_id, doc_node in enumerate(
                    get_doc_nodes(path, doc_node_type, encoding, attr_constraints)):
                if doc_name_from_fn:
                    if file_doc_id == 0:
                        doc_name = base_doc_name
                    else:
                        doc_name = u"{}-{}".format(base_doc_name, file_doc_id)
                else:
                    # The node should supply us with the document name, using the attribute name specified
                    doc_name = doc_node.get(doc_name_attr)
                # Pull the text out of the document node
                doc_text = doc_node.text
                yield doc_name, doc_text


def corpus_iter(reader):
    for doc_name, data in iter_files(reader):
        yield doc_name, reader.datatype.data_point_type(text=data)


@opt_type_help("comma-separated list of key=value constraints")
def key_vals(text):
    if text is None:
        return None
    return dict(key_val.strip().split("=") for key_val in text.split(","))


ModuleInfo = iterable_input_reader(
    {
        "files": {
            "help": "Comma-separated list of absolute paths to files to include in the collection. Paths may include "
                    "globs. Place a '?' at the start of a filename to indicate that it's optional",
            "type": comma_separated_strings,
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
        "document_node_type": {
            "help": "XML node type to extract documents from (default: 'doc')",
            "default": "doc",
        },
        "document_name_attr": {
            "help": "Attribute of document nodes to get document name from. Use special value 'filename' to use the "
                    "filename (without extensions) as a document name. In this case, if there's more than one doc "
                    "in a file, an integer is appended to the doc name after the first doc. (Default: 'filename')",
            "default": "filename",
        },
        "filter_on_doc_attr": {
            "help": "Comma-separated list of key=value constraints. If given, only docs with the attribute 'key' on "
                    "their doc node and the attribute value 'value' will be included",
            "type": key_vals,
        },
    },
    RawTextDocumentType(),
    data_ready, corpus_len, corpus_iter,
    module_type_name="raw_text_files_reader",
    module_readable_name="Raw text files",
    software_dependencies=[beautiful_soup_dependency],
    execute_count=True,
)
