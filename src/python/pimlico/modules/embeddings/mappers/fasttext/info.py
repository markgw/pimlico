# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Use trained fastText embeddings to map words to their embeddings,
including OOVs, using sub-word information.

First train a fastText model using the fastText training module. Then
use this module to produce a doc-embeddings mapper.

"""
from pimlico.core.dependencies.python import PythonPackageOnPip, numpy_dependency, fasttext_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.embeddings import FastTextEmbeddings, FastTextDocMapper


class ModuleInfo(BaseModuleInfo):
    module_type_name = "fasttext_doc_mapper"
    module_readable_name = "fastText to doc-embedding mapper"
    module_inputs = [("embeddings", FastTextEmbeddings())]
    module_outputs = [("mapper", FastTextDocMapper())]
    module_supports_python2 = False

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            fasttext_dependency, numpy_dependency,
        ]
