# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool to split up the output from Caevo and convert it to other datatypes.

Caevo output includes the output from a load of NLP tools that it runs as prerequisites to event extraction, etc.
The individual parts of the output can easily be retrieved from the output corpus via the output datatype. In order
to be able to use them as input to other modules, they need to be converted to compatible standard datatypes.

For example, tokenization output is stored in Caevo's XML output using a special format. Instead of writing
other modules in such a way as to be able to pull this information out of the :class:~pimlico.datatypes.CaevoCorpus,
you can filter the output using this module to provide a :class:~pimlico.datatypes.TokenizedCorpus, which is a
standard format for input to other module types.

As with other document map modules, you can use this as a filter (`filter=T`), so you can actually need to commit
the converted data to disk.

.. todo::

   Add more output convertors: currently only provides tokenization

"""

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import TokenizedCorpus, TokenizedCorpusWriter
from pimlico.datatypes.caevo import CaevoCorpus
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.word_annotations import WordAnnotationCorpusWithRequiredFields, WordAnnotationCorpusWithFields, \
    SimpleWordAnnotationCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "caevo_output"
    module_readable_name = "CAEVO output convertor"
    module_inputs = [("documents", CaevoCorpus)]
    # No stanard outputs -- they're all optional
    module_outputs = []
    module_optional_outputs = [
        ("tokenized", TokenizedCorpus),
        ("parse", ConstituencyParseTreeCorpus),
        ("pos", WordAnnotationCorpusWithFields("word", "pos"))
    ]
    module_options = {
        "gzip": {
            "help": "If True, each output, except annotations, for each document is gzipped. This can help reduce the "
                    "storage occupied by e.g. parser or coref output. Default: False",
            "type": str_to_bool,
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "tokenized":
            return TokenizedCorpusWriter(output_dir, append=append, gzip=self.options["gzip"])
        elif output_name == "parse":
            return ConstituencyParseTreeCorpusWriter(output_dir, append=append, gzip=self.options["gzip"])
        elif output_name == "pos":
            return SimpleWordAnnotationCorpusWriter(output_dir, ["word", "pos"],
                                                    append=append, gzip=self.options["gzip"])
