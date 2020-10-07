# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.dependencies.python import numpy_dependency, scipy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.arrays import ScipySparseMatrix
from pimlico.old_datatypes.features import IndexedTermFeatureListCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_matrix_builder"
    module_readable_name = "Term-feature matrix builder"
    module_inputs = [
        ("data", IndexedTermFeatureListCorpus)
    ]
    module_outputs = [("matrix", ScipySparseMatrix)]
    module_options = {}
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            numpy_dependency, scipy_dependency
        ]
