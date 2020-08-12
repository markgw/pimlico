# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Reads in text from the Ubuntu Dialogue Corpus.

"""
import io
import json
import os
from itertools import islice

from pimlico.core.modules.inputs import iterable_input_reader
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


def iter_dialogue_json(options):
    path = options["path"]
    limit = options["limit"]

    with io.open(path, "r") as f:
        data = json.load(f)

    # Use the dialogue IDs as doc names where possible, but make sure they're unique
    used_doc_names = set()

    for dia_json in islice(data, limit):
        doc_name = dia_json["dialogue_id"]

        # Keep increasing the distinguishing ID until we have a unique name
        base_doc_name = doc_name
        distinguish_id = 0
        while doc_name in used_doc_names:
            doc_name = "{}-{}".format(base_doc_name, distinguish_id)
            distinguish_id += 1
        used_doc_names.add(doc_name)

        yield doc_name, dia_json


def data_ready(options):
    return os.path.exists(options["path"])


def corpus_len(options):
    return sum(1 for __ in iter_dialogue_json(options))


def iter_dialogues(reader):
    options = reader.options

    for doc_name, dia_json in iter_dialogue_json(options):
        yield doc_name, dia_json["text"]


def corpus_iter(reader):
    for doc_name, data in iter_dialogues(reader):
        yield doc_name, reader.datatype.data_point_type(text=data)


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
    RawTextDocumentType(),
    data_ready, corpus_len, corpus_iter,
    module_type_name="ubuntu_dialogue_reader",
    module_readable_name="Ubuntu Dialogue Corpus reader",
    python2=True,
)
