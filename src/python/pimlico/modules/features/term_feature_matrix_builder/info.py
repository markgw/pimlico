# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
from pimlico.core.dependencies.python import numpy_dependency, scipy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.arrays import ScipySparseMatrix
from pimlico.datatypes.features import IndexedTermFeatureListCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_matrix_builder"
    module_readable_name = "Term-feature matrix builder"
    module_inputs = [
        ("data", IndexedTermFeatureListCorpus)
    ]
    module_outputs = [("matrix", ScipySparseMatrix)]
    module_options = {}

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            numpy_dependency, scipy_dependency
        ]
