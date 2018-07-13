# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Provides a simple interface to `Scikit-Learn's <http://scikit-learn.org/stable/>`_ various matrix factorization
models.

Since they provide a consistent training interface, you can simply choose the class name of the method you
want to use and specify options relevant to that method in the ``options`` option. For available options,
take a look at the table of parameters in the
`Scikit-Learn documentation <http://scikit-learn.org/stable/modules/classes.html#module-sklearn.decomposition>`_
for each class.

"""
import json

from pimlico.core.config import PipelineConfigParseError
from pimlico.core.dependencies.python import PythonPackageOnPip
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list
from pimlico.datatypes.arrays import ScipySparseMatrix, NumpyArray


SKLEARN_CLASSES = {
    "PCA": {
        "sparse": False,
    },
    "ProjectedGradientNMF": {
        "sparse": True
    },
    "RandomizedPCA": {
        "sparse": True,
    },
    "FactorAnalysis": {
        "sparse": False,  # I think...?
    },
    "FastICA": {
        "sparse": False,  # Don't know
    },
    "TruncatedSVD": {
        "sparse": True,
    },
    "NMF": {
        "sparse": True,
    },
    "SparsePCA": {
        "sparse": True,  # That's the point...
    },
    "LatentDirichletAllocation": {
        "sparse": True,
    },
}


class ModuleInfo(BaseModuleInfo):
    module_type_name = "sklearn_mat_fac"
    module_readable_name = "Sklearn matrix factorization"
    module_inputs = [("matrix", ScipySparseMatrix)]
    module_outputs = [("w", NumpyArray), ("h", NumpyArray)]
    module_options = {
        "class": {
            "help": "Scikit-learn class to use to fit the matrix factorization. Should be the name of a class in "
                    "the package sklearn.decomposition that has a fit_transform() method and a components\\_ attribute. "
                    "Supported classes: %s" % ", ".join(SKLEARN_CLASSES),
            "type": choose_from_list(SKLEARN_CLASSES.keys()),
            "required": True,
        },
        "options": {
            "help": "Options to pass into the constructor of the sklearn class, formatted as a JSON dictionary "
                    "(potentially without the {}s). E.g.: 'n_components=200, solver=\"cd\", tol=0.0001, max_iter=200'",
        },
    }

    def __init__(self, module_name, pipeline, **kwargs):
        super(ModuleInfo, self).__init__(module_name, pipeline, **kwargs)
        # Process JSON options
        json_options = self.options["options"].strip()
        # Add {}s if they're not in the input, to make the input format potentially nicer looking
        if not json_options[0] == "{" or not json_options[-1] == "}":
            json_options = "{%s}" % json_options
        try:
            self.init_kwargs = json.loads(json_options)
        except ValueError:
            raise PipelineConfigParseError("could not parse JSON options for scikit-learn module: %s" % json_options)
        # Try loading the given transformer class name to check it's a valid one
        try:
            self.load_transformer_class()
        except ImportError, e:
            raise PipelineConfigParseError("Could not load decomposition class %s. Check it's available in the version "
                                           "of scikit-learn you have installed" % self.options["class"])

    def load_transformer_class(self):
        from sklearn import decomposition
        return getattr(decomposition, self.options["class"])

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [PythonPackageOnPip("sklearn", "Scikit-learn")]
