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

        self.log.info("Collecting stats")
        character_count = 0
        sent_count = 0
        token_counter = Counter()

        pbar = get_progress_bar(len(corpus), title="Counting")
        for __, doc in pbar(corpus):
            if not is_invalid_doc(doc):
                sent_count += len(doc.sentences)
                for sent in doc.sentences:
                    # Add counts of each word
                    token_counter.update(sent)
                    # Count the characters in the tokens, plus spaces between them
                    character_count += sum(len(token) for token in sent) + len(sent) - 1

        self.log.info("{:,} characters".format(character_count))
        type_count = len(token_counter)
        token_count = sum(token_counter.values())
        self.log.info("{:,} types".format(type_count))
        self.log.info("{:,} tokens".format(token_count))
        self.log.info("{:,} sentences".format(sent_count))
        self.log.info("{:.2f} characters per sentence".format(float(character_count) / sent_count))
        self.log.info("{:.2f} tokens per sentence".format(float(token_count) / sent_count))

        data = {
            "types": type_count,
            "tokens": token_count,
            "sentences": sent_count,
            "characters": character_count,
        }

        with self.info.get_output_writer("stats") as writer:
            writer.write_file(json.dumps(data, indent=4), text=True)
            self.log.info("Stats output to %s" % writer.absolute_path)
