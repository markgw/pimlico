# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.dictionary import Dictionary
from pimlico.old_datatypes.features import IndexedTermFeatureListCorpus, TermFeatureListDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_vocab_mapper"
    module_readable_name = "Term-feature corpus vocab mapper"
    module_inputs = [
        ("data", TarredCorpusType(TermFeatureListDocumentType)),
        ("term_vocab", Dictionary), ("feature_vocab", Dictionary)
    ]
    module_outputs = [("data", IndexedTermFeatureListCorpus)]
    module_options = {}
    module_supports_python2 = True
