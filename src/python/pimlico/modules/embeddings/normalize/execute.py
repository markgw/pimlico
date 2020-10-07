# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError

import numpy as np


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_embeddings = self.info.get_input("embeddings")
        # If more normalizations are added, replace this by a check that at least something is applied
        if not self.info.options["l2_norm"]:
            raise ModuleExecutionError("no normalizations have been selected")

        embeddings = input_embeddings.vectors
        if self.info.options["l2_norm"]:
            # Apply L2 normalization
            norms = np.sqrt(np.sum(embeddings ** 2., axis=1))
            embeddings /= norms[:, np.newaxis]

        with self.info.get_output_writer("embeddings") as writer:
            self.log.info("Writing vectors")
            writer.write_vectors(embeddings)
            self.log.info("Writing word counts")
            writer.write_word_counts(input_embeddings.word_counts)
