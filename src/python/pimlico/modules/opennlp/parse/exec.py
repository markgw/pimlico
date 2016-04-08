from py4j.java_collections import ListConverter

from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Start a tokenizer process
        self.coref = StreamParser(self.info.model_path, pipeline=self.info.pipeline)
        try:
            self.coref.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting coref process: %s" % e)
        # Just get raw data from the input iterator, to skip splitting on spaces and then joining again
        self.input_corpora[0].raw_data = True

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Input is a raw string: split on newlines to get tokenized sentences
        sentences = doc.splitlines()
        # Run parser on these sentences
        parses = self.coref.parse(sentences)
        return parses

    def postprocess(self, error=False):
        self.coref.stop()
        self.coref = None


class StreamParser(object):
    def __init__(self, model_path, pipeline=None):
        self.pipeline = pipeline
        self.model_path = model_path
        self.interface = None

    def parse(self, sentences):
        """
        Parse input sentences, a list of strings, which should be tokenized with tokens separated by spaces.

        """
        sentence_list = ListConverter().convert(sentences, self.interface.gateway._gateway_client)
        return list(self.interface.gateway.entry_point.parseTrees(sentence_list))

    def start(self):
        # Start a parser process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.ParserGateway", gateway_args=[self.model_path],
                                       pipeline=self.pipeline)
        self.interface.start()

    def stop(self):
        self.interface.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class PosTaggerProcessError(Exception):
    pass
