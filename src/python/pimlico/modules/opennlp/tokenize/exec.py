from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Start a tokenizer process
        self.tokenizer = StreamTokenizer(self.info.sentence_model_path, self.info.token_model_path,
                                         pipeline=self.info.pipeline)
        try:
            self.tokenizer.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting tokenizer process: %s" % e)

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Run tokenization
        tokenized_sents = self.tokenizer.tokenize(doc)
        # Output one sentence per line
        return u"\n".join(tokenized_sents)

    def postprocess(self, error=False):
        self.tokenizer.stop()
        self.tokenizer = None


class StreamTokenizer(object):
    def __init__(self, sentence_model_path, token_model_path, pipeline=None):
        self.pipeline = pipeline
        self.token_model_path = token_model_path
        self.sentence_model_path = sentence_model_path

        self.interface = None

    def tokenize(self, document):
        return list(self.interface.gateway.entry_point.tokenize(document))

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[self.sentence_model_path, self.token_model_path],
                                       pipeline=self.pipeline)
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
