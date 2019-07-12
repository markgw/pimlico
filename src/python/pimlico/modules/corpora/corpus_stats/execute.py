# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import json
from collections import Counter

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")

        self.log.info("Counting characters")
        pbar = get_progress_bar(len(corpus), title="Counting")
        characters = sum(sum(len(token) for token in sent) + len(sent)
                         for doc_name, doc in pbar(corpus) if not is_invalid_doc(doc) for sent in doc.sentences)
        self.log.info("{:,} characters".format(characters))

        self.log.info("Counting tokens")
        pbar = get_progress_bar(len(corpus), title="Counting")
        token_count = Counter(token for doc_name, doc in pbar(corpus) if not is_invalid_doc(doc)
                              for sent in doc.sentences for token in sent)

        types = len(token_count)
        tokens = sum(token_count.values())

        self.log.info("{:,} types".format(types))
        self.log.info("{:,} tokens".format(tokens))

        self.log.info("Counting sentences")
        pbar = get_progress_bar(len(corpus), title="Counting")
        sent_count = sum(len(doc.sentences) for doc_name, doc in pbar(corpus) if not is_invalid_doc(doc))

        self.log.info("{:,} sentences".format(sent_count))
        self.log.info("{:.2f} characters per sentence".format(float(characters) / sent_count))
        self.log.info("{:.2f} tokens per sentence".format(float(tokens) / sent_count))

        data = {
            "types": types,
            "tokens": tokens,
            "sentences": sent_count,
            "characters": characters,
        }

        with self.info.get_output_writer("stats") as writer:
            writer.write_file(json.dumps(data, indent=4), text=True)
            self.log.info("Stats output to %s" % writer.absolute_path)
