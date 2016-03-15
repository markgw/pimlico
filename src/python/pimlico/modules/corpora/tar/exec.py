from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.tar import TarredCorpusWriter
from pimlico.modules.corpora.tar_filter.info import TarredCorpusFilter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self, module_instance_info):
        # Most of what we need to do is implemented by the filter version of this module, so reuse that
        filter_datatype = TarredCorpusFilter(
            module_instance_info.get_input("documents"),
            module_instance_info.options["archive_size"],
            archive_basename=module_instance_info.options["archive_basename"]
        )
        
        # Create a writer to do the writing to disk
        with TarredCorpusWriter(module_instance_info.get_output_dir()) as writer:
            for archive_name, doc_name, doc in filter_datatype.archive_iter():
                writer.add_document(archive_name, doc_name, doc)
