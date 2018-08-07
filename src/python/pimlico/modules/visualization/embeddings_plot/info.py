# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Plot vectors from embeddings, trained by some other module, in a 2D space
using a MDS reduction and Matplotlib.

They might, for example, come from :mod:`pimlico.modules.embeddings.word2vec`. The embeddings are
read in using Pimlico's generic word embedding storage type.

Uses scikit-learn to perform the MDS/TSNE reduction.

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import json_string, choose_from_list, comma_separated_strings
from pimlico.old_datatypes.base import MultipleInputs
from pimlico.old_datatypes.embeddings import Embeddings
from pimlico.old_datatypes.plotting import PlotOutput
from pimlico.modules.visualization import matplotlib_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "embeddings_plot"
    module_readable_name = "Embedding space plotter"
    module_inputs = [("vectors", MultipleInputs(Embeddings))]
    module_outputs = [("plot", PlotOutput)]
    module_options = {
        "words": {
            "help": "Number of most frequent words to plot. Default: 50",
            "default": 50,
            "type": int,
        },
        "skip": {
            "help": "Number of most frequent words to skip, taking the next most frequent after these. Default: 0",
            "default": 0,
            "type": int,
        },
        "cmap": {
            "help": "Mapping from word prefixes to matplotlib plotting colours. Every word beginning with the given "
                    "prefix has the prefix removed and is plotted in the corresponding colour. Specify as a JSON "
                    "dictionary mapping prefix strings to colour strings",
            "type": json_string,
        },
        "colors": {
            "help": "List of colours to use for different embedding sets. Should be a list of matplotlib colour "
                    "strings, one for each embedding set given in input_vectors",
            "type": comma_separated_strings,
        },
        "metric": {
            "help": "Distance metric to use. Choose from 'cosine', 'euclidean', 'manhattan'. Default: 'cosine'",
            "type": choose_from_list(["cosine", "euclidean", "manhattan"]),
            "default": "cosine",
        },
        "reduction": {
            "help": "Dimensionality reduction technique to use to project to 2D. Available: mds (Multi-dimensional "
                    "Scaling), tsne (t-distributed Stochastic Neighbor Embedding). Default: mds",
            "type": choose_from_list(["mds", "tsne"]),
            "default": "mds",
        },
    }

    def get_software_dependencies(self):
        return [matplotlib_dependency, sklearn_dependency]
