from pimlico.core.external.java import Py4JInterface
from pimlico.core.modules.map import DocumentMapModuleExecutor
from py4j.java_collections import ListConverter


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self, info):
        start_port = info.pipeline.local_config.get("py4j_start_port", None)
        start_port = int(start_port) if start_port is not None else None
        # Start a tokenizer process
        self.tagger = StreamTagger(info.model_path, start_port=start_port)
        self.tagger.start()

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
    def __init__(self, model_path, start_port=None):
        self.start_port = start_port
        self.model_path = model_path
        self.interface = None

    def tag(self, sentences):
        sentence_list = ListConverter().convert(sentences, self.interface.gateway._gateway_client)
        return list(self.interface.gateway.entry_point.posTag(sentence_list))

    def start(self):
        if self.start_port is None:
            python_port = None
        else:
            python_port = self.start_port + 1

        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.PosTaggerGateway", gateway_args=[self.model_path],
                                       port=self.start_port, python_port=python_port)
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
