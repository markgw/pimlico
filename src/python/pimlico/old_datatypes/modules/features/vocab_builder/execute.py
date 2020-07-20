# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.old_datatypes.dictionary import DictionaryWriter
from pimlico.utils.progress import get_progress_bar

from src.python.pimlico.datatypes.corpora.data_points import is_invalid_doc


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_docs = self.info.get_input("term_features")
        self.log.info("Building dictionaries from terms and features in %d docs" % len(input_docs))
        pbar = get_progress_bar(len(input_docs), title="Counting")

        # Prepare dictionary writers for the term and feature vocabs
        with DictionaryWriter(self.info.get_absolute_output_dir("term_vocab")) as term_vocab_writer:
            with DictionaryWriter(self.info.get_absolute_output_dir("feature_vocab")) as feature_vocab_writer:
                # Input is given for every document in a corpus
                for doc_name, document in pbar(input_docs):
                    if not is_invalid_doc(document):
                        # Update the term vocab with all terms in this doc
                        term_vocab_writer.add_documents([[term for (term, fcs) in document]])
                        # Update the feature vocab with all features with non-zero counts
                        feature_vocab_writer.add_documents([
                            [feature for (t, feature_counts) in document
                             for (feature, count) in feature_counts.items() if count > 0]
                        ])

                # Filter the vocabs according to the options set
                self.log.info("Built dictionaries (terms=%d, features=%d), applying filters" %
                              (len(term_vocab_writer.data), len(feature_vocab_writer.data)))

                self.log.info("Feature vocab filters: %s" % ", ".join("%s=%s" % (k, v) for (k, v) in [
                    ("threshold", self.info.options["feature_threshold"]),
                    ("max proportion", self.info.options["feature_max_prop"]),
                    ("limit", self.info.options["feature_limit"]),
                ] if v is not None))
                feature_vocab_writer.filter(
                    self.info.options["feature_threshold"],
                    self.info.options["feature_max_prop"],
                    self.info.options["feature_limit"]
                )
                self.log.info("Outputting feature vocab (%d features)" % len(feature_vocab_writer.data))

            self.log.info("Term vocab filters: %s" % ", ".join("%s=%s" % (k, v) for (k, v) in [
                ("threshold", self.info.options["term_threshold"]),
                ("max proportion", self.info.options["term_max_prop"]),
                ("limit", self.info.options["term_limit"]),
            ] if v is not None))
            term_vocab_writer.filter(
                self.info.options["term_threshold"],
                self.info.options["term_max_prop"],
                self.info.options["term_limit"]
            )
            self.log.info("Outputting term vocab (%d terms)" % len(term_vocab_writer.data))
