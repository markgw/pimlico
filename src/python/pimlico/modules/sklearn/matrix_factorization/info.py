import json

from pimlico.core.config import PipelineConfigParseError
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list
from pimlico.datatypes.arrays import ScipySparseMatrix, NumpyArray
from pimlico.modules.sklearn import check_sklearn_dependency


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
    module_inputs = [("matrix", ScipySparseMatrix)]
    module_outputs = [("w", NumpyArray), ("h", NumpyArray)]
    module_options = {
        "class": {
            "help": "Scikit-learn class to use to fit the matrix factorization. Should be the name of a class in "
                    "the package sklearn.decomposition that has a fit_transform() method and a components_ attribute. "
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

    def load_transformer_class(self):
        from sklearn import decomposition
        return getattr(decomposition, self.options["class"])

    def check_runtime_dependencies(self):
        missing_dependencies = check_sklearn_dependency(self.module_name) + \
                               super(ModuleInfo, self).check_runtime_dependencies()
        try:
            self.load_transformer_class()
        except ImportError, e:
            missing_dependencies.append(("Sklearn class %s" % "sklearn.decomposition.%s" % self.options["class"],
                                         self.module_name,
                                         "Could not load decomposition class %s. Check it's available in the version "
                                         "of scikit-learn you have installed" % self.options["class"]))
        return missing_dependencies
