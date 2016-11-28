from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.ints import IntegerListsDocumentCorpus, IntegerListsDocumentCorpusWriter
from pimlico.datatypes.tar import TarredCorpusType
from pimlico.datatypes.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "vocab_mapper"
    module_readable_name = "Tokenized corpus to ID mapper"
    module_inputs = [("text", TarredCorpusType(TokenizedDocumentType)), ("vocab", Dictionary)]
    module_outputs = [("ids", IntegerListsDocumentCorpus)]

    def get_writer(self, output_name, output_dir, append=False):
        return IntegerListsDocumentCorpusWriter(output_dir, signed=False, bytes=4, append=append)