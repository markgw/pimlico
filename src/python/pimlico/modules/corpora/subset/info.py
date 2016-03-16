"""
Simple filter to truncate a dataset after a given number of documents, potentially offsetting by a number
of documents. Mainly useful for creating small subsets of a corpus for testing a pipeline before running
on the full corpus.

"""
from itertools import islice

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import IterableDocumentCorpus


class CorpusSubsetFilter(IterableDocumentCorpus):
    def __init__(self, input_datatype, size, offset=0):
        IterableDocumentCorpus.__init__(self, None)

        self.offset = offset
        self.input_datatype = input_datatype
        self.size = size

    def __len__(self):
        return min(self.size, len(self.input_datatype))

    def __iter__(self):
        return islice(self.input_datatype, self.offset, self.offset+self.size)

    def data_ready(self):
        return True


class ModuleInfo(BaseModuleInfo):
    module_type_name = "subset"
    module_inputs = [("documents", IterableDocumentCorpus)]
    module_outputs = [("documents", CorpusSubsetFilter)]
    module_options = [
        ("size", {
            "help": "Number of documents to include",
            "required": True,
        }),
        ("offset", {
            "help": "Number of documents to skip at the beginning of the corpus (default: 0, start at beginning)",
            "default": 0,
        }),
    ]
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype):
        if output_name == "documents":
            return CorpusSubsetFilter(self.get_input("documents"), self.options["size"], offset=self.options["offset"])
        else:
            return super(ModuleInfo, self).instantiate_output_datatype(output_name, output_datatype)
