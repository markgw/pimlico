import os

from pimlico.core.dependencies.python import numpy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.embeddings import Embeddings


class ModuleInfo(BaseModuleInfo):
    """
    Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
    them in the format used internally in Pimlico for embeddings.

    Can be used, for example, to read the
    `pre-trained embeddings <https://github.com/facebookresearch/fastText/blob/master/pretrained-vectors.md>`_
    offered by Facebook AI.

    Currently only reads the text format (``.vec``), not the binary format (``.bin``).

    .. seealso::

       :mod:`pimlico.modules.input.embeddings.fasttext_gensim`:
          An alternative reader that uses Gensim's FastText format reading code and permits reading from the
          binary format, which contains more information.

    .. todo::

       Update to new datatypes system and add test pipeline

    """
    module_type_name = "fasttext_embedding_reader"
    module_readable_name = "FastText embedding reader"
    module_outputs = [("embeddings", Embeddings)]
    module_options = {
        "path": {
            "help": "Path to the FastText embedding file",
            "required": True,
        },
        "limit": {
            "help": "Limit to the first N words. Since the files are typically ordered from most to least frequent, "
                    "this limits to the N most common words",
            "type": int,
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [numpy_dependency]

    def missing_module_data(self):
        missing = super(ModuleInfo, self).missing_module_data()
        if not os.path.exists(self.options["path"]):
            missing.append("input file for {}".format(self.module_name))
        return missing
