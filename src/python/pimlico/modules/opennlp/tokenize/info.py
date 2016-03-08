from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import IterableDocumentCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "opennlp_tokenizer"
    module_inputs = [("text", IterableDocumentCorpus)]

