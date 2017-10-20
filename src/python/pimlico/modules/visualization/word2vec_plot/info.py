# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Plot vectors from word2vec embeddings trained by :mod:`pimlico.modules.embeddings.word2vec` in a 2D space
using a MDS reduction and Matplotlib.

Uses scikit-learn to perform the MDS reduction.

"""
from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.plotting import PlotOutput
from pimlico.datatypes.word2vec import Word2VecModel
from pimlico.modules.visualization import matplotlib_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "word2vec_plot"
    module_readable_name = "Gensim word2vec plotter"
    module_inputs = [("vectors", Word2VecModel)]
    module_outputs = [("plot", PlotOutput)]
    module_options = {
        "words": {
            "help": "Number of most frequent words to plot. Default: 50",
            "default": 50,
            "type": int,
        },
    }

    def get_software_dependencies(self):
        return [matplotlib_dependency, sklearn_dependency]
