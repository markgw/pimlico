# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_embeddings = self.info.get_input("embeddings")

        with self.info.get_output_writer("mapper") as writer:
            writer.save_model(input_embeddings.load_model())
