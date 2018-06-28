from pimlico.core.dependencies.python import gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.embeddings import Embeddings
from pimlico.datatypes.files import NamedFileCollection, NamedFileCollectionWriter


class Word2VecFiles(NamedFileCollection):
    datatype_name = "word2vec_files"
    filenames = ["embeddings.bin", "embeddings.vocab"]


class Word2VecFilesWriter(NamedFileCollectionWriter):
    filenames = ["embeddings.bin", "embeddings.vocab"]


class ModuleInfo(BaseModuleInfo):
    """
    Takes embeddings stored in the default format used within Pimlico pipelines
    (see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
    using the ``word2vec`` storage format.

    Uses the Gensim implementation of the storage, so depends on Gensim.

    """
    module_type_name = "store_word2vec"
    module_readable_name = "Store in word2vec format"
    module_inputs = [("embeddings", Embeddings)]
    module_outputs = [("embeddings", Word2VecFiles)]

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [gensim_dependency]
