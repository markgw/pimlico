# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import json
from collections import Counter

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")

        self.log.info("Collecting stats")
        token_counter = Counter()
        sents_per_doc = StatCollector()
        tokens_per_doc = StatCollector()
        chars_per_sent = StatCollector()
        tokens_per_sent = StatCollector()

        pbar = get_progress_bar(len(corpus), title="Counting")
        for __, doc in pbar(corpus):
            if not is_invalid_doc(doc):
                sents_per_doc.count(len(doc.sentences))
                tokens_per_doc.count(sum(len(sent) for sent in doc.sentences))

                for sent in doc.sentences:
                    # Add counts of each word
                    token_counter.update(sent)
                    # Count the characters in the tokens, plus spaces between them
                    chars_per_sent.count(sum(len(token) for token in sent) + len(sent) - 1)
                    tokens_per_sent.count(len(sent))

        character_count = chars_per_sent.total
        self.log.info("{:,} characters".format(character_count))
        type_count = len(token_counter)
        token_count = sum(token_counter.values())
        self.log.info("{:,} types".format(type_count))
        self.log.info("{:,} tokens".format(token_count))
        sent_count = sents_per_doc.total
        self.log.info("{:,} sentences".format(sent_count))
        self.log.info("{:.2f} characters per sentence (min {}, max {})".format(
            chars_per_sent.mean(), chars_per_sent.min, chars_per_sent.max))
        self.log.info("{:.2f} tokens per sentence (min {}, max {})".format(
            tokens_per_sent.mean(), tokens_per_sent.min, tokens_per_sent.max))
        self.log.info("{:.2f} sentences per doc (min {}, max {})".format(
            sents_per_doc.mean(), sents_per_doc.min, sents_per_doc.max))
        self.log.info("{:.2f} tokens per doc (min {}, max {})".format(
            tokens_per_doc.mean(), tokens_per_doc.min, tokens_per_doc.max))

        data = {
            "types": type_count,
            "tokens": token_count,
            "sentences": sent_count,
            "characters": character_count,
            "mean chars per sent": chars_per_sent.mean(),
            "min chars per sent": chars_per_sent.min,
            "max chars per sent": chars_per_sent.max,
            "mean tokens per sent": tokens_per_sent.mean(),
            "min tokens per sent": tokens_per_sent.min,
            "max tokens per sent": tokens_per_sent.max,
            "mean sents per doc": sents_per_doc.mean(),
            "min sents per doc": sents_per_doc.min,
            "max sents per doc": sents_per_doc.max,
            "mean tokens per doc": tokens_per_doc.mean(),
            "min tokens per doc": tokens_per_doc.min,
            "max tokens per doc": tokens_per_doc.max,
        }

        with self.info.get_output_writer("stats") as writer:
            writer.write_file(json.dumps(data, indent=4), text=True)
            self.log.info("Stats output to %s" % writer.absolute_path)


class StatCollector:
    def __init__(self):
        self.total = 0
        self.n = 0
        self.min = None
        self.max = None

    def count(self, val):
        self.total += val
        self.n += 1
        if self.min is None or val < self.min:
            self.min = val
        if self.max is None or val > self.max:
            self.max = val

    def mean(self):
        return float(self.total) / self.n