from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import Embeddings, TSVVecFiles


class ModuleInfo(BaseModuleInfo):
    """
    Takes embeddings stored in the default format used within Pimlico pipelines
    (see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
    as TSV files.

    This is for using the vectors outside your pipeline, for example, for
    distributing them publicly or using as input to an external visualization
    tool. For passing embeddings between Pimlico modules,
    the internal :class:`~pimlico.datatypes.embeddings.Embeddings` datatype
    should be used.

    These are suitable as input to the `Tensorflow Projector <https://projector.tensorflow.org/>`_.

    """
    module_type_name = "store_tsv"
    module_readable_name = "Store in TSV format"
    module_inputs = [("embeddings", Embeddings())]
    module_outputs = [("embeddings", TSVVecFiles())]
