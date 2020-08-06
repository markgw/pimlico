"""
Simply stores embeddings in the Pimlico internal format.

This is not often needed, but can be useful if reading embeddings for an
input reader that is slower than reading from the internal format. Then
you can use this module to do the reading and store the result before
passing it to other modules.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.embeddings import Embeddings


class ModuleInfo(BaseModuleInfo):
    module_type_name = "store_embeddings"
    module_readable_name = "Store embeddings (internal)"
    module_inputs = [("embeddings", Embeddings())]
    module_outputs = [("embeddings", Embeddings())]
    module_supports_python2 = True
