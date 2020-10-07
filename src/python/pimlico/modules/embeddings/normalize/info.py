# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Apply normalization to a set of word embeddings.

For now, only one type of normalization is provided: L2 normalization.
Each vector is scaled so that its Euclidean magnitude is 1.

Other normalizations (like L1 or variance normalization) may be added in future.

"""
from pimlico.core.dependencies.python import numpy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes.embeddings import Embeddings


class ModuleInfo(BaseModuleInfo):
    module_type_name = "normalize_embeddings"
    module_readable_name = "Normalize embeddings"
    module_inputs = [("embeddings", Embeddings())]
    module_outputs = [("embeddings", Embeddings())]
    module_options = {
        "l2_norm": {
            "help": "Apply L2 normalization to scale each vector to unit length. Default: T",
            "default": True,
            "type": str_to_bool,
        },
    }
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [numpy_dependency]
