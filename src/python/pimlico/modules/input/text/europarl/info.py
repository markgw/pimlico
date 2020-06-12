# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Input reader for raw, unaligned text from Europarl corpus. This does not cover the automatically
aligned versions of the corpus that are typically used for Machine Translation.

The module takes care of a bit of extra processing specific to cleaning up the Europarl data.

.. seealso::

   :mod:`~pimlico.modules.input.text.raw_text_files`, which this extends with special postprocessing.

"""
import re

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.datatypes.corpora import invalid_document
from pimlico.datatypes.corpora.data_points import RawTextDocumentType
from pimlico.modules.input.text.raw_text_files.info import data_ready as raw_data_ready, \
    corpus_len as raw_corpus_len, corpus_iter as raw_corpus_iter, ModuleInfo as raw_module_info

language_indicator_re = re.compile(r"\([A-Z]{2}\) ")


def filter_line(line):
    """
    Filter applied to each line. It either returns an updated version of the line, or None, in which
    case the line is left out altogether.

    """
    if line.startswith("<"):
        # Simply filter out all lines beginning with '<', which are metadata
        return None

    # Some metadata-like text is also included at the start of lines, followed by ". - "
    if ". - " in line:
        __, __, line = line.partition(". - ")

    # Remove -s and spaces from the start of lines
    # Not sure why they're often there, but it's just how the transcripts were formatted
    line = line.lstrip("- ")

    # Skip lines that are fully surrounded by brackets: they're typically descriptions of what happened
    # E.g. (Applause)
    if line.startswith("(") and line.endswith(")"):
        return None

    # It's common for a speaker's first utterance to start with a marker indicating the original language
    line = language_indicator_re.sub("", line)
    return line


def filter_text(doc):
    text = doc.text
    lines = [filter_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line is not None]
    # If a document has only a couple of lines in it, it's not a debate transcript, but just a heading
    # Better to skip these
    if len(lines) < 4:
        return invalid_document("europarl_reader",
                                error_info="Too few lines in document: not a debate transcript")
    return doc.data_point_type(text="\n".join(lines))


def corpus_iter(reader):
    # Use the raw text files iterator and just post-process the docs
    for doc_name, doc in raw_corpus_iter(reader):
        yield doc_name, filter_text(doc)


ModuleInfo = iterable_input_reader(
    raw_module_info.module_options,
    RawTextDocumentType(),
    raw_data_ready, raw_corpus_len, corpus_iter,
    module_type_name="europarl_reader",
    module_readable_name="Europarl corpus reader",
)
