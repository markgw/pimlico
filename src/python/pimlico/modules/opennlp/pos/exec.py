from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from py4j.java_collections import ListConverter


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Start a tokenizer process
        self.tagger = StreamTagger(self.info.model_path, pipeline=self.info.pipeline)
        try:
            self.tagger.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting tagger process: %s" % e)

        # Check that the input provides us with words
        if isinstance(self.input_corpora[0], WordAnnotationCorpus):
            available_fields = self.input_corpora[0].read_annotation_fields()
            if "word" not in available_fields:
                raise ModuleExecutionError("input datatype does not provide a field 'word' -- can't POS tag it")

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Input is a list of tokenized sentences
        # Run POS tagging
        tags = self.tagger.tag([" ".join(sentence) for sentence in doc])
        # Put the POS tags together with the words
        # The writer will format them to look like word|POS
        return [
            zip(sentence_words, sentence_tags.split())
            for (sentence_words, sentence_tags) in zip(doc, tags)
        ]

    def postprocess(self, error=False):
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
