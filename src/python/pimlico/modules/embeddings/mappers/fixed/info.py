# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Use trained fixed word embeddings to map words to their embeddings.
Does nothing with OOVs, which we don't have any way to map.

First train or load embeddings using another module.
Then use this module to produce a doc-embeddings mapper.

"""
from pimlico.core.dependencies.python import numpy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import Embeddings
from pimlico.datatypes.embeddings import FixedEmbeddingsDocMapper


class ModuleInfo(BaseModuleInfo):
    module_type_name = "fixed_embeddings_doc_mapper"
    module_readable_name = "Fixed embeddings to doc-embedding mapper"
    module_inputs = [("embeddings", Embeddings())]
    module_outputs = [("mapper", FixedEmbeddingsDocMapper())]
    module_supports_python2 = False

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [numpy_dependency]
