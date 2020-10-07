# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import range
from collections import Counter

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_set_up(worker):
    worker.model = worker.info.get_input("model").load_model()


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # Get a bag of words for the document
    bow = list(Counter(word for sentence in doc.lists for word in sentence).items())
    # Use the LDA model to infer a topic vector for the document
    topic_weights = dict(worker.model[bow])
    # The weights are a sparse vector: fill in the relevant values and leave the rest as 0
    return {"vector": [topic_weights.get(i, 0.) for i in range(worker.model.num_topics)]}


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_set_up)
