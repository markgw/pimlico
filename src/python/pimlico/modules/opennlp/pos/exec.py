from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor
from py4j.java_collections import ListConverter


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self, info):
        # Start a tokenizer process
        self.tagger = StreamTagger(info.model_path, pipeline=info.pipeline)
        try:
            self.tagger.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting tokenizer process: %s" % e)

    def process_document(self, filename, doc):
        sentences = doc.splitlines()
        # Run POS tagging
        tags = self.tagger.tag(sentences)
        # Put the POS tags together with the words, as it makes them easier to use
        tagged_sents = [
            u" ".join([u"%s|%s" % (word, tag) for (word, tag) in zip(sentence_words.split(), sentence_tags.split())])
            for (sentence_words, sentence_tags) in zip(sentences, tags)
        ]
        # Output one sentence per line
        return u"".join("%s\n" % sent for sent in tagged_sents)

    def postprocess(self, info, error=False):
        self.tagger.stop()
        self.tagger = None


class StreamTagger(object):
    def __init__(self, model_path, pipeline=None):
        self.pipeline = pipeline
        self.model_path = model_path
        self.interface = None

    def tag(self, sentences):
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
