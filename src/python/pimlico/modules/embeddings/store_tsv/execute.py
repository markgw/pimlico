# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        embeddings = self.info.get_input("embeddings")

        # Output to the file
        with self.info.get_output_writer("embeddings") as writer:
            writer.write_vectors(embeddings.vectors)
            writer.write_vocab_with_counts(embeddings.word_counts)
