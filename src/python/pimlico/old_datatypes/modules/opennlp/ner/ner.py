# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import object
from py4j.java_collections import ListConverter

from pimlico.core.external.java import Py4JInterface


class NERTagger(object):
    def __init__(self, model_path, pipeline=None):
        self.model_path = model_path
        self.pipeline = pipeline

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.NERGateway", gateway_args=[self.model_path],
                                       pipeline=self.pipeline, print_stderr=False, print_stdout=False)
        self.interface.start()
        self.gateway = self.interface.gateway

    def stop(self):
        self.interface.stop()

    def tag_sentences(self, doc):
        # Input is a list of tokenized sentences
        sentence_list = ListConverter().convert([" ".join(sentence) for sentence in doc], self.gateway._gateway_client)
        # Run NER tagging
        spans = self.gateway.entry_point.nerFind(sentence_list)
        spans = [[(s.getStart(), s.getEnd()) for s in sentence_spans] for sentence_spans in spans]
        return spans
