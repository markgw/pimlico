# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.dictionary import DictionaryWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_docs = self.info.get_input("text")
        self.log.info("Building dictionary from %d docs" % len(input_docs))
        pbar = get_progress_bar(len(input_docs), title="Counting")

        # Prepare dictionary writers for the term and feature vocabs
        with DictionaryWriter(self.info.get_absolute_output_dir("vocab")) as vocab_writer:
            # Input is given for every document in a corpus
            for doc_name, document in pbar(input_docs):
                if not isinstance(document, InvalidDocument):
                    # Update the term vocab with all terms in this doc
                    vocab_writer.add_documents(document)

            # Filter the vocab according to the options set
            self.log.info("Built dictionary of %d terms, applying filters" % len(vocab_writer.data))

            self.log.info("Feature vocab filters: %s" % ", ".join("%s=%s" % (k, v) for (k, v) in [
                ("threshold", self.info.options["threshold"]),
                ("max proportion", self.info.options["max_prop"]),
                ("limit", self.info.options["limit"]),
            ] if v is not None))
            vocab_writer.filter(
                self.info.options["threshold"],
                self.info.options["max_prop"],
                self.info.options["limit"]
            )

            if self.info.options["include"] is not None:
                # Guarantee inclusion of certain terms
                self.log.info("Guaranteeing inclusion of %s" % ", ".join(self.info.options["include"]))
                for term in self.info.options["include"]:
                    vocab_writer.data.add_term(term)

            self.log.info("Outputting vocab (%d terms)" % len(vocab_writer.data))
