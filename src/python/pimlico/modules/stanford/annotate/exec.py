from pimlico.core.modules.map import DocumentMapModuleExecutor
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus
from pimlico.modules.stanford import CoreNLPProcessingError
from pimlico.modules.stanford.wrapper import CoreNLP


def _word_annotation_preproc(doc):
    return "\n".join(" ".join(word["word"] for word in sentence) for sentence in doc)


class ModuleExecutor(DocumentMapModuleExecutor):
    def get_writer(self, info):
        output_name, output_datatype = info.get_output_datatype("documents")
        return SimpleWordAnnotationCorpusWriter(info.get_output_dir("documents"), output_datatype.annotation_fields)

    def preprocess(self, info):
        annotators = []
        if not isinstance(self.input_corpora[0], (WordAnnotationCorpus, TokenizedCorpus)):
            # Data not already run through a tokenizer: include tokenization and sentence splitting
            annotators.extend(["tokenize", "ssplit"])
        annotators.extend(info.options["annotators"].split(","))

        # By default, for a TarredCorpus or TokenizedCorpus, just pass in the document text
        self._doc_preproc = lambda doc: doc
        if type(self.input_corpora[0]) is TokenizedCorpus:
            # Just get the raw text data, which we happen to know is tokenized
            self.input_corpora[0].raw_data = True
        elif isinstance(self.input_corpora[0], WordAnnotationCorpus):
            # For a word annotation corpus, we need to pull out the words
            self._doc_preproc = _word_annotation_preproc

        # Prepare the list of attributes to extract from the output and send to the writer
        output_name, output_datatype = info.get_output_datatype("documents")
        self.output_fields = output_datatype.annotation_fields

        # Prepare a CoreNLP background process to do the processing
        self.corenlp = CoreNLP(info.pipeline)
        self.corenlp.start()
        self.log.info("CoreNLP server started on %s" % self.corenlp.server_url)
        self.properties = {
            "annotators": ",".join(annotators),
            "outputFormat": "json",
        }

    def process_document(self, archive, filename, doc):
        doc = self._doc_preproc(doc)

        if doc.strip():
            # Call CoreNLP on the doc
            try:
                json_result = self.corenlp.annotate(doc.encode("utf-8"), self.properties)
            except CoreNLPProcessingError, e:
                # TODO: do something other than re-raise
                raise

            return [
                [
                    [word_data[field_name] for field_name in self.output_fields]
                    for word_data in sentence["tokens"]
                ] for sentence in json_result["sentences"]
            ]
        else:
            return []

    def postprocess(self, info, error=False):
        self.corenlp.shutdown()
