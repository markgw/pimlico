from pimlico.core.external.java import Py4JInterface
from pimlico.core.modules.map import DocumentMapModuleExecutor


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self, info):
        # Start a tokenizer process
        self.tokenizer = StreamTokenizer(info.sentence_model_path, info.token_model_path)
        self.tokenizer.start()

    def process_document(self, filename, doc):
        # Run tokenization
        tokenized_sents = self.tokenizer.tokenize(doc)
        # Output one sentence per line
        return u"".join("%s\n" % sent for sent in tokenized_sents)

    def postprocess(self, info, error=False):
        self.tokenizer.stop()
        self.tokenizer = None


class StreamTokenizer(object):
    def __init__(self, sentence_model_path, token_model_path):
        self.token_model_path = token_model_path
        self.sentence_model_path = sentence_model_path

        self.interface = None

    def tokenize(self, document):
        return list(self.interface.gateway.entry_point.tokenize(document))

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[self.sentence_model_path, self.token_model_path])
        self.interface.start()

    def stop(self):
        self.interface.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class TokenizerProcessError(Exception):
    pass
