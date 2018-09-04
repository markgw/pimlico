# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Provides an interface to `Scikit-Learn's <http://scikit-learn.org/stable/>`_ simple
`logistic regression <scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html>`_
trainer.

You may also want to consider using:

 - `LogisticRegressionCV <scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegressionCV.html>`_:
   LR with cross-validation to choose regularization strength

 - `SGDClassifier <scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html>`_:
   general gradient-descent training for classifiers, which includes logistic regression.
   A better choice for training on a large dataset.

"""

from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import json_dict
from pimlico.datatypes.features import ScoredRealFeatureSets
from pimlico.datatypes.sklearn import SklearnModel


class ModuleInfo(BaseModuleInfo):
    module_type_name = "sklearn_log_reg"
    module_readable_name = "Sklearn logistic regression"
    module_inputs = [("features", ScoredRealFeatureSets())]
    module_outputs = [("model", SklearnModel())]
    module_options = {
        "options": {
            "help": "Options to pass into the constructor of LogisticRegression, formatted as a JSON dictionary "
                    "(potentially without the {}s). E.g.: '\"C\":1.5, \"penalty\":\"l2\"'",
            "type": json_dict,
            "default": {},
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [sklearn_dependency]
