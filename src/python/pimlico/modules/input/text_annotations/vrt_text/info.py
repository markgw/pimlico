# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Input reader for VRT text collections (`VeRticalized Text, as used by Korp:
<https://www.kielipankki.fi/development/korp/corpus-input-format/#VRT_file_format>`_), just for
reading the (tokenized) text content, throwing away all the annotations.

Uses sentence tags to divide each text into sentences.


.. seealso::

   :mod:`pimlico.modules.input.text_annotations.vrt`:
      Reading VRT files with all their annotations

.. todo::

   Update to new datatypes system and add test pipeline

.. todo::

   Currently skipped from module doc generator, until updated

"""
import io
import os

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.modules.input.text.raw_text_files.info import ModuleInfo as RawTextModuleInfo, \
    data_ready as rt_data_ready, get_paths_from_options
from pimlico.modules.input.text_annotations.vrt.read import VRTText


def count_documents(options):
    """
    Counts length of corpus. Each file can contain an arbitrary number of documents.
    Should only be called after data_ready() == True.

    All documents are considered valid, even if they have no content, so the valid
    of valid docs supplied during the counting process is the same as the total
    number of docs.

    """
    count = 0
    for doc_name, path, start, end in get_paths_from_options(options):
        if os.path.exists(path):
            # Scan through the lines of the file to find all lines that start a new document
            with open(path, "r") as f:
                for line in f:
                    if line.startswith(u"<text "):
                        count += 1
    # Num docs, num valid docs
    return count


def iter_docs_in_file(f):
    """
    We need to split each file into multiple docs

    Note that the file could be huge, e.g. the whole corpus, so avoid reading it all into memory.
    """
    current_text = []
    for line in f:
        if line.startswith(u"<text "):
            # Start of a new text
            # If there's anything in the buffer, there must have been a missing closing tag. Throw it away
            current_text = [line]
        elif line.startswith(u"</text>"):
            # End of text: yield it
            current_text.append(line)
            yield u"".join(current_text).strip(u"\n")
            current_text = []
        else:
            # Mid-text
            current_text.append(line)


def corpus_iter(reader):
    options = reader.options

    encoding = options["encoding"]
    # Use the file basenames as doc names where possible, but make sure they're unique
    used_doc_names = set()
    for file_doc_name, path, start, end in get_paths_from_options(options):
        if file_doc_name is None:
            file_doc_name = os.path.basename(path)
            distinguish_id = 0
            # Keep increasing the distinguishing ID until we have a unique name
            while file_doc_name in used_doc_names:
                base, ext = os.path.splitext(file_doc_name)
                file_doc_name = "%s-%d%s" % (base, distinguish_id, ext)
                distinguish_id += 1
            used_doc_names.add(file_doc_name)

        with io.open(path, "r", encoding=encoding, errors=options["encoding_errors"]) as f:
            for doc_id_in_file, doc_text in enumerate(iter_docs_in_file(f)):
                doc_name = "{}-{}".format(file_doc_name, doc_id_in_file)
                # Parse the VRT data to get sentences of tokenized words
                vrt = VRTText.from_string(doc_text)
                # Pull sentences of raw word strings out of that
                sentences = [[word.word for word in sentence] for sentence in vrt.sentences]
                yield doc_name, reader.datatype.data_point_type(sentences=sentences)


ModuleInfo = iterable_input_reader(
    dict(RawTextModuleInfo.module_options, **{
        # More options may be added here
    }),
    TokenizedDocumentType(),
    rt_data_ready, count_documents, corpus_iter,
    module_type_name="vrt_files_reader",
    module_readable_name="VRT annotated text files",
    execute_count=True,
)
