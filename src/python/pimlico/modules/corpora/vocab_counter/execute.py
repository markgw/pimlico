# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import range
from collections import Counter

import numpy
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import InvalidDocument, is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        corpus = self.info.get_input("corpus")
        vocab = self.info.get_input("vocab").get_data()
        dist_len = len(vocab)+1 if self.info.options["oov_excluded"] else len(vocab)

        self.log.info("Counting token frequencies in corpus")
        pbar = get_progress_bar(len(corpus))
        # Iterate over the whole corpus, counting up tokens
        counts = Counter(
            token for doc_name, doc in pbar(corpus) if not is_invalid_doc(doc)
            for line in doc.lists for token in line
        )
        self.log.info("Counts collected")
        # Put the result in a numpy array
        dist = numpy.array([counts.get(i, 0) for i in range(dist_len)])

        # Store the output array
        with self.info.get_output_writer("distribution") as writer:
            writer.write_array(dist)

        # Output most and least frequent tokens
        ordered_ids = list(reversed(numpy.argsort(dist)))
        _id2token = lambda i: "OOV" if i >= len(vocab) else vocab.id2token[i]
        _fmt_ids = lambda ids: u", ".join(u"{} ({})".format(_id2token(i), dist[i]) for i in ids)
        self.log.info(u"{}, ..., {}".format(_fmt_ids(ordered_ids[:5]), _fmt_ids(ordered_ids[-5:])))
