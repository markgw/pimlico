from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list
from pimlico.datatypes.arrays import ScipySparseMatrix, NumpyArray
from pimlico.modules.sklearn import check_sklearn_dependency


SKLEARN_CLASSES = [
    "PCA", "ProjectedGradientNMF", "RandomizedPCA", "FactorAnalysis", "FastICA", "TruncatedSVD",
    "NMF", "SparsePCA", "LatentDirichletAllocation",
]


class ModuleInfo(BaseModuleInfo):
    module_type_name = "sklearn_mat_fac"
    module_inputs = [("matrix", ScipySparseMatrix)]
    module_outputs = [("w", NumpyArray), ("h", NumpyArray)]
    module_options = {
        "class": {
            "help": "Scikit-learn class to use to fit the matrix factorization. Should be the name of a class in "
                    "the package sklearn.decomposition that has a fit_transform() method and a components_ attribute. "
                    "Supported classes: %s" % ", ".join(SKLEARN_CLASSES),
            "type": choose_from_list(SKLEARN_CLASSES),
            "required": True,
        },
        "options": {
            "help": "Options to pass into the constructor of the sklearn class, formatted as a JSON dictionary "
                    "(potentially without the {}s). E.g.: 'n_components=200, solver=\"cd\", tol=0.0001, max_iter=200'",
        },
    }

    def check_runtime_dependencies(self):
        return check_sklearn_dependency(self.module_name) + super(ModuleInfo, self).check_runtime_dependencies()
