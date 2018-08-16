# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Store a corpus

Take documents from a corpus and write them to disk using the standard
writer for the corpus' data point type. This is
useful where documents are produced on the fly, for example from some filter
module or from an input reader, but where it is desirable to store the
produced corpus for further use, rather than always running the filters/readers
each time the corpus' documents are needed.

.. todo::

   Added test pipeline: get it working!

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.corpora import GroupedCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "store"
    module_readable_name = "Store a corpus"
    module_inputs = [("corpus", GroupedCorpus())]
    module_outputs = [("corpus", GroupedCorpusWithTypeFromInput())]

    def get_output_writer(self, output_name=None, **kwargs):
        # Include metadata from the input in the writer kwargs
        kwargs.update(self.get_input("corpus").metadata)
        return super(ModuleInfo, self).get_output_writer(output_name, **kwargs)
