# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os

from pimlico.core.dependencies.python import numpy_dependency, PythonPackageOnPip, fasttext_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.embeddings import Embeddings, FastTextEmbeddings


class ModuleInfo(BaseModuleInfo):
    """
    Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
    them in the format used internally in Pimlico for embeddings.

    Loads the fastText ``.bin`` format using the fasttext library itself. Outputs
    both a fixed set of embeddings in Pimlico's standard format and a special
    fastText datatype that provides access to more features of the model.

    """
    module_type_name = "fasttext_bin_embedding_reader"
    module_readable_name = "FastText embedding reader (bin)"
    module_outputs = [("embeddings", Embeddings()), ("model", FastTextEmbeddings())]
    module_options = {
        "path": {
            "help": "Path to the FastText embedding file",
            "required": True,
        },
    }
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [numpy_dependency, fasttext_dependency]

    def missing_module_data(self):
        missing = super(ModuleInfo, self).missing_module_data()
        if not os.path.exists(self.options["path"]):
            missing.append("input file for {}".format(self.module_name))
        return missing
