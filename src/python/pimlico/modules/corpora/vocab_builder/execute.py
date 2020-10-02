# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from __future__ import unicode_literals

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_docs = self.info.get_input("text")
        oov_token = self.info.options["oov"]

        # Read an optional list of stopwords
        stopwords = self.info.get_input("stopwords")
        if stopwords is not None:
            stopwords = stopwords.get_list()
            self.log.info("Initial list of {:,} stopwords".format(len(stopwords)))

        prune_at = self.info.options["prune_at"] or None
        if prune_at is not None:
            self.log.info("Pruning if dictionary size reaches {}".format(prune_at))

        self.log.info("Building dictionary from %d docs" % len(input_docs))
        pbar = get_progress_bar(len(input_docs), title="Counting")

        # Prepare dictionary writers for the term and feature vocabs
        # Set the list of stopwords initially, so that these terms will be
        #  ignored while building the vocab
        with self.info.get_output_writer("vocab", stopwords=stopwords) as vocab_writer:
            # Input is given for every document in a corpus
            # Update the term vocab with all terms in each doc
            vocab_writer.add_documents(
                (sum(doc.sentences, []) for doc_name, doc in pbar(input_docs) if not is_invalid_doc(doc)),
                prune_at=prune_at
            )

            # Filter the vocab according to the options set
            self.log.info("Built dictionary of {:,} terms, applying filters".format(len(vocab_writer.data)))

            self.log.info("Feature vocab filters: {}".format(", ".join("{}={}".format(k, v) for (k, v) in [
                ("threshold", self.info.options["threshold"]),
                ("max proportion", self.info.options["max_prop"]),
                ("limit", self.info.options["limit"]),
            ] if v is not None)))
            removed_freq, removed_rare = vocab_writer.filter_high_low(
                self.info.options["threshold"],
                self.info.options["max_prop"],
                self.info.options["limit"]
            )
            show_removed_freq = removed_freq[:30] + [("...", None, None)] if len(removed_freq) > 30 else removed_freq
            show_removed_rare = removed_rare[:30] + [("...", None, None)] if len(removed_rare) > 30 else removed_rare
            self.log.info("Filters removed {:,} frequent items from vocabulary: {}".format(
                len(removed_freq), ", ".join(char for (char, __, __) in show_removed_freq)
            ))
            self.log.info("Filters removed {:,} rare items from vocabulary: {}".format(
                len(removed_rare), ", ".join(char for (char, __, __) in show_removed_rare)
            ))

            if self.info.options["include"] is not None:
                # Guarantee inclusion of certain terms
                self.log.info("Guaranteeing inclusion of %s" % ", ".join(self.info.options["include"]))
                for term in self.info.options["include"]:
                    vocab_writer.data.add_term(term)

            if oov_token:
                # Add the OOV token to the vocabulary
                oov_id = vocab_writer.data.add_term(oov_token)
                # To get a correct document count for the OOV token, we need to go over the
                # data again and check where the filtered-out terms appear
                self.log.info("Counting OOVs in the input corpus")
                pbar = get_progress_bar(len(input_docs), title="Counting OOVs")
                vocab_terms = set(vocab_writer.data.token2id.keys())
                oov_count = sum(
                    (1 if any(
                        word not in vocab_terms
                        for line in doc.sentences
                        for word in line)
                     else 0 for dn, doc in pbar(input_docs) if not is_invalid_doc(doc)), 0
                )
                vocab_writer.data.dfs[oov_id] = oov_count
                self.log.info("Added OOV token '{}' with count of {:,}".format(oov_token, oov_count))

            self.log.info("Outputting vocab ({} terms)".format(len(vocab_writer.data)))

            stopwords = list(vocab_writer.data.stopwords)

        self.log.info("Final list of {:,} stopwords".format(len(stopwords)))
        with self.info.get_output_writer("stopwords") as stopwords_writer:
            stopwords_writer.write_list(stopwords)
