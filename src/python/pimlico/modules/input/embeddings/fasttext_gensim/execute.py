# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from gensim.models.wrappers.fasttext import FastText

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]

        # Use Gensim's tool to load the data
        self.log.info("Loading FastText vectors from {}".format(path))
        fasttext = FastText.load_fasttext_format(path)

        # Get the vectors from the model
        # We can use these to store embeddings in the Pimlico format
        # This will throw away information specific to FastText (the things added in the FastTextKeyedVectors class)
        with self.info.get_output_writer() as writer:
            self.log.info("Writing embeddings to {}".format(writer.base_dir))
            writer.write_keyed_vectors(fasttext.wv)
