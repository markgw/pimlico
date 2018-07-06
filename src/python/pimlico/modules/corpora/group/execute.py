# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.corpora.group_filter.info import TarredCorpusFilter


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
        with self.info.get_output_writer("documents") as writer:
            for archive_name, doc_name, doc in filter_datatype.archive_iter():
                writer.add_document(archive_name, doc_name, doc)
