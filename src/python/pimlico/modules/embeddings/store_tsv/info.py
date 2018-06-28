from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.embeddings import Embeddings, TSVVecFiles


class ModuleInfo(BaseModuleInfo):
    """
    Takes embeddings stored in the default format used within Pimlico pipelines
    (see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
    as TSV files.

    These are suitable as input to the [Tensorflow Projector](https://projector.tensorflow.org/).

    """
    module_type_name = "store_tsv"
    module_readable_name = "Store in TSV format"
    module_inputs = [("embeddings", Embeddings)]
    module_outputs = [("embeddings", TSVVecFiles)]
