# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import object
from pimlico.core.external.java import Py4JInterface


class Tokenizer(object):
    """
    Set sentence_model_path=None to skip sentence splitting.

    """
    def __init__(self, sentence_model_path, token_model_path, pipeline=None):
        self.sentence_model_path = sentence_model_path
        self.pipeline = pipeline
        self.token_model_path = token_model_path

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[self.sentence_model_path or "none", self.token_model_path],
                                       pipeline=self.pipeline, print_stderr=False, print_stdout=False)
        self.interface.start()
        # Open a client gateway to the executor's py4j interface
        self.gateway = self.interface.gateway

    def stop(self):
        self.interface.stop()

    def tokenize_text(self, text):
        """
        Takes a block of text and divides it into sentences and tokenizes.
        Returns a list of sentences, where each is tokenized, with tokens separated by spaces.

        """
        tokenized_sents = list(self.gateway.entry_point.tokenize(text))
        sents = [s.split(u" ") for s in tokenized_sents]
        return sents
