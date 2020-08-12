# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Reads in year+month labels from the Ubuntu Dialogue Corpus.

Note that the corpus is expected to already be sorted by date.

"""
from datetime import datetime

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.datatypes.corpora.strings import LabelDocumentType
from ..ubuntu_dialogue.info import iter_dialogue_json, data_ready, corpus_len


def iter_labels(reader):
    options = reader.options

    for doc_name, dia_json in iter_dialogue_json(options):
        # Parse the timestamp to extract the year and month
        ts = datetime.strptime(dia_json["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
        yield doc_name, "{:04d}-{:02d}".format(ts.year, ts.month)


def corpus_iter(reader):
    for doc_name, data in iter_labels(reader):
        yield doc_name, reader.datatype.data_point_type(label=data)


ModuleInfo = iterable_input_reader(
    {
        "path": {
            "help": "Path the JSON input file",
            "required": True,
        },
        "limit": {
            "type": int,
            "help": "Truncate the corpus after this number of documents",
        },
    },
    LabelDocumentType(),
    data_ready, corpus_len, corpus_iter,
    module_type_name="raw_text_files_reader",
    module_readable_name="Raw text files",
    python2=True,
)
