import os

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import Embeddings


class ModuleInfo(BaseModuleInfo):
    """
    Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
    them in the format used internally in Pimlico for embeddings. This version uses Gensim's implementation
    of the format reader, so depends on Gensim.

    Can be used, for example, to read the
    `pre-trained embeddings <https://github.com/facebookresearch/fastText/blob/master/pretrained-vectors.md>`_
    offered by Facebook AI.

    Reads only the binary format (``.bin``), not the text format (``.vec``).

    .. seealso::

       :mod:`pimlico.modules.input.embeddings.fasttext`:
          An alternative reader that does not use Gensim. It permits (only) reading the text format.

    .. todo::

       Add test pipeline. This is slightly difficult, as we need a small FastText binary
       file, which is harder to produce, since you can't easily just truncate a big file.

    """
    module_type_name = "fasttext_embedding_reader_gensim"
    module_readable_name = "FastText embedding reader (Gensim)"
    module_outputs = [("embeddings", Embeddings())]
    module_options = {
        "path": {
            "help": "Path to the FastText embedding file (.bin)",
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
