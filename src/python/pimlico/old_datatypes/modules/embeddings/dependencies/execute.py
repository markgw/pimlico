# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from collections import Counter

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    document_features = []

    # Each item in the doc is a sentence
    for sentence in doc:
        word_field = "lemma" if worker.info.options["lemma"] else "word"
        # Build an index of the words in the sentence, so we can look up heads
        words = dict((fields["id"], fields) for fields in sentence)
        word_features = {}

        # TODO
        # Catch prepositional modifiers and tied them up with what they're modifying
        #if head_row[7] == "prep" and int(head_row[6]) != 0:
        #    yield filter_word(row[1]), "adpmod:%s_%s" % (filter_word(head_row[1]),
        #                                                 filter_word(rows[int(head_row[6])-1][1]))
        # You can do this as a pre-processing step on the dependencies

        for token in sentence:
            # Skip dependencies of the root node
            if token["head"] == 0:
                continue
            # Skip any dependency types we've been told to ignore
            if token["deprel"] in worker.info.options["skip_types"]:
                continue

            head_token = words[token["head"]]
            pos = token["postag"]
            head_pos = head_token["postag"]
            dep_type = token["deprel"]

            # Might be only interested in certain POS tags
            if not worker.info.filter_pos \
                    or pos in worker.info.include_tags \
                    or any(pos.startswith(t) for t in worker.info.include_tag_prefixes):
                # Build a feature out of the dep type and head word
                word_features.setdefault(token["id"], []).append("%s_%s" % (dep_type, head_token[word_field]))

            # Also include inverted deps
            # Filter similarly on POS tags
            if not worker.info.filter_pos \
                    or head_pos in worker.info.include_tags \
                    or any(head_pos.startswith(t) for t in worker.info.include_tag_prefixes):
                word_features.setdefault(head_token["id"], []).append("%sI_%s" % (dep_type, token[word_field]))

            # Replace the word indices with words
            document_features.extend(
                (words[word_idx][word_field], dict(Counter(features)))
                for (word_idx, features) in word_features.items()
            )
    return document_features


ModuleExecutor = multiprocessing_executor_factory(process_document)
