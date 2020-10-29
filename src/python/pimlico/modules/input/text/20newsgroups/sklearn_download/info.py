"""
Input reader to fetch the 20 Newsgroups dataset from Sklearn.
See: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_20newsgroups.html

The original data can be downloaded from http://qwone.com/~jason/20Newsgroups/.

"""
from pimlico.datatypes.corpora.ints import IntegerDocumentType

from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list, str_to_bool, comma_separated_strings
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "20ng_fetcher"
    module_readable_name = "20 Newsgroups fetcher (sklearn)"
    module_inputs = []
    module_outputs = [
        ("text", GroupedCorpus(RawTextDocumentType())),
        ("labels", GroupedCorpus(IntegerDocumentType())),
    ]
    module_options = {
        "subset": {
            "help": "Select the dataset to load: ‘train’ for the training set, ‘test’ for the test set, ‘all’ for "
                    "both, with shuffled ordering",
            "type": choose_from_list(["train", "test", "all"]),
            "default": "train",
        },
        "shuffle": {
            "help": "Whether or not to shuffle the data: might be important for models that make the assumption "
                    "that the samples are independent and identically distributed (i.i.d.), such as "
                    "stochastic gradient descent",
            "type": str_to_bool,
        },
        "random_state": {
            "help": "Determines random number generation for dataset shuffling. Pass an int for reproducible "
                    "output across multiple runs",
            "type": int,
        },
        "remove": {
            "help": "May contain any subset of (‘headers’, ‘footers’, ‘quotes’). Each of these are kinds of text "
                    "that will be detected and removed from the newsgroup posts, preventing classifiers from "
                    "overfitting on metadata",
            "type": comma_separated_strings,
        },
        "limit": {
            "help": "Truncate corpus",
            "type": int,
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [sklearn_dependency]
