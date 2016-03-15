from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.tar import TarredCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_tokenizer"
    module_inputs = [("text", TarredCorpus)]

