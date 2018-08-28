import os

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import Embeddings


class ModuleInfo(BaseModuleInfo):
    """
    Reads in embeddings from the `GloVe <https://nlp.stanford.edu/projects/glove/>`_ format, storing
    them in the format used internally in Pimlico for embeddings. We use Gensim's implementation
    of the format reader, so the module depends on Gensim.

    Can be used, for example, to read the pre-trained embeddings
    `offered by Stanford <https://nlp.stanford.edu/projects/glove/>`_.

    Note that the format is almost identical to `word2vec`'s text format.

    """
    module_type_name = "word2vec_embedding_reader"
    module_readable_name = "Word2vec embedding reader using Gensim"
    module_outputs = [("embeddings", Embeddings())]
    module_options = {
        "path": {
            "help": "Path to the GloVe embedding file",
            "required": True,
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [gensim_dependency]

    def missing_module_data(self):
        missing = super(ModuleInfo, self).missing_module_data()
        if not os.path.exists(self.options["path"]):
            missing.append("input file for {}".format(self.module_name))
        return missing
