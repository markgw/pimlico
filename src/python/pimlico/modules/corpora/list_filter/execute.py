# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("corpus")

        pbar = get_progress_bar(len(input_corpus), title="Filtering")
        set1_list = self.info.get_input("list").data

        with self.info.get_output_writer("set1", **input_corpus.metadata) as set1_writer:
            with self.info.get_output_writer("set2", **input_corpus.metadata) as set2_writer:
                for archive_name, doc_name, doc_data in pbar(input_corpus.archive_iter()):
                    if doc_name in set1_list:
                        put_in = set1_writer
                    else:
                        put_in = set2_writer
                    put_in.add_document(archive_name, doc_name, doc_data)
