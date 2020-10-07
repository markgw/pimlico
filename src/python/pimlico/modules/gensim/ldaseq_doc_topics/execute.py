# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
I would prefer to implement this by getting a static LDA model for
each time slice during pre-processing and then running super-fast LDA
inference for each document, using the appropriate model. In principle,
this is doable. However, Gensim's current DTM implementation (and
LDA implementation) doesn't make it easy.

However, we do something like this by creating an LDA model for each
slice and then using LDAPost with that to do the inference

"""
from collections import Counter

import numpy as np
import logging

from gensim.models import ldamodel
from gensim.models.ldaseqmodel import LdaPost

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def get_slice_ldas(dtm):
    ldas = []
    for slice_num in range(dtm.num_time_slices):
        lda_model = ldamodel.LdaModel(
            num_topics=dtm.num_topics, alpha=dtm.alphas, id2word=dtm.id2word, dtype=np.float64)
        lda_model.topics = np.zeros((dtm.vocab_len, dtm.num_topics))
        # Get DTM's parameters for one time slice and attach them to this LDAModel
        dtm.make_lda_seq_slice(lda_model, slice_num)
        ldas.append(lda_model)
    return ldas


def get_doc_topics(dtm, lda, doc, slice_num):
    # Use LDAPost to do the inference for this time slice only
    ldapost = LdaPost(num_topics=dtm.num_topics, max_doc_len=len(doc), lda=lda, doc=doc)
    LdaPost.fit_lda_post(ldapost, slice_num, None, dtm)
    # Get the result
    doc_topic = ldapost.gamma / ldapost.gamma.sum()
    return doc_topic


@skip_invalid
def process_document(worker, archive_name, doc_name, doc, label_doc):
    # Get a bag of words for the document
    bow = list(Counter(word for sentence in doc.lists for word in sentence).items())
    # Work out what slice this doc should use
    slice = worker.label_to_slice[label_doc.label]
    # Get the LDA model for this time slice
    #lda_model = worker.slice_ldas[slice]
    # Use the LDA model to infer a topic vector for the document
    #topic_weights = dict(lda_model[bow])
    # Infer doc topics for just this time slice
    topic_weights = get_doc_topics(worker.model, worker.slice_ldas[slice], bow, slice)
    ## The weights are a sparse vector: fill in the relevant values and leave the rest as 0
    #return {"vector": [topic_weights.get(i, 0.) for i in range(worker.model.num_topics)]}
    return {"vector": topic_weights}


def worker_set_up(worker):
    model_reader = worker.info.get_input("model")
    worker.model = model_reader.load_model()
    worker.labels = model_reader.load_labels()
    # Load the labels for the time slices and prepare the mapping to slice indices
    worker.label_to_slice = dict((label, slice) for (slice, label) in enumerate(worker.labels))
    # Before creating LDAModels, silence the ldamodel logger, so we don't get loads of output
    logging.getLogger("gensim.models.ldamodel").setLevel(logging.ERROR)
    # Prepare LDA models for each time slice
    worker.slice_ldas = get_slice_ldas(worker.model)


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_set_up)
