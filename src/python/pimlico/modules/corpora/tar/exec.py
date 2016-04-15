from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.tar import TarredCorpusWriter
from pimlico.modules.corpora.tar_filter.info import TarredCorpusFilter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        # Most of what we need to do is implemented by the filter version of this module, so reuse that
        filter_datatype = TarredCorpusFilter(
            self.info.pipeline,
            self.info.get_input("documents"),
            self.info.options["archive_size"],
            archive_basename=self.info.options["archive_basename"]
        )
        
        # Create a writer to do the writing to disk
        with TarredCorpusWriter(self.info.get_module_output_dir(short_term_store=True)) as writer:
            for archive_name, doc_name, doc in filter_datatype.archive_iter():
                writer.add_document(archive_name, doc_name, doc)
