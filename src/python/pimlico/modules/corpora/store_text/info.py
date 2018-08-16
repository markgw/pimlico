# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Store a text corpus

Take documents from a text corpus and write them to disk as text. This is
useful where the text is produced on the fly, for example from some filter
module or from an input reader, but where it is desirable to store the
produced text as a simple text corpus for further use.

.. note::

   In the new datatype system, this can be replaced by a generic version
   of a `store` module that stores documents using the writing functionality
   of whatever datatype they are in. This can't be done generically in the
   old datatype system.

.. todo::

   Add test pipeline and test it

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.corpora import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType, TextDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "store_text"
    module_readable_name = "Store a text corpus"
    module_inputs = [("corpus", GroupedCorpus(TextDocumentType()))]
    module_outputs = [("text", GroupedCorpus(RawTextDocumentType()))]
