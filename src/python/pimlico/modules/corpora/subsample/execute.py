import random

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("corpus")
        skip_invalid = self.info.options["skip_invalid"]
        prob = self.info.options["p"]
        if prob > 1.:
            # Treat as a target output size
            target_size = int(prob)
            prob = target_size / len(input_corpus)
            if prob > 1.:
                self.log.warn("Target size of {:,} resulted in a sampling probability of {}: input size is {:,}. "
                              "All documents will be included"
                              .format(target_size, prob, len(input_corpus)))

        rng = random.Random(self.info.options["seed"])
        selected = 0
        total = 0

        with self.info.get_output_writer("corpus") as writer:
            self.log.info("Randomly sampling docs with a probability of {:.2f}% from corpus of {:,} docs"
                          .format(prob*100., len(input_corpus)))
            pbar = get_progress_bar(len(input_corpus), title="Sampling")
            for archive_name, doc_name, doc in pbar(input_corpus.archive_iter()):
                # If skipping invalid, check this now
                if not skip_invalid or not is_invalid_doc(doc):
                    total += 1
                    if rng.random() < prob:
                        # Include this document
                        writer.add_document(archive_name, doc_name, doc)
                        selected += 1

        self.log.info("Included {:,}/{:,} docs in output corpus".format(selected, total))
