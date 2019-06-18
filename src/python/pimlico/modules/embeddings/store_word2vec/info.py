from pimlico.core.dependencies.python import gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import Embeddings
from pimlico.datatypes.embeddings import Word2VecFiles


class ModuleInfo(BaseModuleInfo):
    """
    Takes embeddings stored in the default format used within Pimlico pipelines
    (see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
    using the ``word2vec`` storage format.

    This is for using the vectors outside your pipeline, for example, for
    distributing them publicly. For passing embeddings between Pimlico modules,
    the internal :class:`~pimlico.datatypes.embeddings.Embeddings` datatype
    should be used.

    The output contains a ``bin`` file, containing the vectors in the binary
    format, and a ``vocab`` file, containing the vocabulary and word counts.

    Uses the Gensim implementation of the storage, so depends on Gensim.

    """
    module_type_name = "store_word2vec"
    module_readable_name = "Store in word2vec format"
    module_inputs = [("embeddings", Embeddings())]
    module_outputs = [("embeddings", Word2VecFiles())]

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [gensim_dependency]
