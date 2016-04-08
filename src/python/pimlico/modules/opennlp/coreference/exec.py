from py4j.java_collections import ListConverter

from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Start a tokenizer process
        self.coref = StreamResolver(self.info.model_path, pipeline=self.info.pipeline)
        try:
            self.coref.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting coref process: %s" % e)

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Input is a list of parse trees
        # Run coref
        tags = self.coref.coref_resolve([" ".join(sentence) for sentence in doc])
        # TODO Work out what to output
        return [
            zip(sentence_words, sentence_tags.split())
            for (sentence_words, sentence_tags) in zip(doc, tags)
        ]

    def postprocess(self, error=False):
        self.coref.stop()
        self.coref = None


class StreamResolver(object):
    def __init__(self, model_path, pipeline=None):
        self.pipeline = pipeline
        self.model_path = model_path
        self.interface = None

    def coref_resolve(self, sentences):
        # TODO Do conversion
        sentence_list = ListConverter().convert(sentences, self.interface.gateway._gateway_client)
        return list(self.interface.gateway.entry_point.posTag(sentence_list))

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.PosTaggerGateway", gateway_args=[self.model_path],
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
