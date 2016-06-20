from pimlico.core.external.java import Py4JInterface


class Tokenizer(object):
    def __init__(self, sentence_model_path, token_model_path, pipeline=None):
        self.sentence_model_path = sentence_model_path
        self.pipeline = pipeline
        self.token_model_path = token_model_path

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[self.sentence_model_path, self.token_model_path],
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
        return self.gateway.entry_point.tokenize(text.encode("utf-8"))
