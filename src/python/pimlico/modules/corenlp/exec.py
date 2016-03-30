from pimlico.core.modules.map import DocumentMapModuleExecutor
from pimlico.datatypes.parse import ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from pimlico.modules.corenlp import CoreNLPProcessingError
from pimlico.modules.corenlp.wrapper import CoreNLP
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


def _word_annotation_preproc(doc):
    return [" ".join(word["word"] for word in sentence) for sentence in doc]


class ModuleExecutor(DocumentMapModuleExecutor):
    def get_writer(self, output_name):
        if output_name == "annotations":
            output_name, output_datatype = self.info.get_output_datatype(output_name)
            return SimpleWordAnnotationCorpusWriter(self.info.get_output_dir(output_name),
                                                    output_datatype.annotation_fields)
        elif output_name == "parse":
            # Just write out parse trees as they come from the parser
            return ConstituencyParseTreeCorpusWriter(self.info.get_output_dir(output_name))
        else:
            raise ValueError("unknown output '%s'" % output_name)

    def preprocess(self):
        annotators = []
        # TODO Work out how to pass in annotations already done if they're given
        if not isinstance(self.input_corpora[0], (WordAnnotationCorpus, TokenizedCorpus)):
            # Data not already run through a tokenizer: include tokenization and sentence splitting
            annotators.extend(["tokenize", "ssplit"])
        annotators.extend(self.info.options["annotators"].split(","))

        if "parse" in self.info.output_names:
            # We need the parser to be run
            # If POS tagging hasn't been included, add it in for the parser's sake
            # TODO Don't do this if POS tags are supplied in the input, once I've worked out how to feed them in
            if "pos" not in annotators:
                annotators.append("pos")
            annotators.append("parse")

        # By default, for a TarredCorpus or TokenizedCorpus, just pass in the document text
        if isinstance(self.input_corpora[0], WordAnnotationCorpus):
            # For a word annotation corpus, we need to pull out the words
            self._doc_preproc = _word_annotation_preproc
        elif isinstance(self.input_corpora[0], TokenizedCorpus):
            # Just get the raw text data, which we happen to know is tokenized
            self.input_corpora[0].raw_data = True
            # Since it's tokenized (and sentence split) we can divide it up into sentences
            self._doc_preproc = lambda doc: doc.split("\n") if doc.strip() else []
        else:
            # Input's not already tokenized, so the best we can do is split it on blank lines
            self._doc_preproc = lambda doc: doc.split("\n\n") if doc.strip() else []

        # Prepare the list of attributes to extract from the output and send to the writer
        if "annotations" in self.info.output_names:
            self.output_fields = self.info.get_output_datatype("annotations")[1].annotation_fields
        else:
            self.output_fields = None

        # Prepare a CoreNLP background process to do the processing
        self.corenlp = CoreNLP(self.info.pipeline)
        self.corenlp.start()
        self.log.info("CoreNLP server started on %s" % self.corenlp.server_url)
        self.properties = {
            "annotators": ",".join(annotators),
            "outputFormat": "json",
        }

    def process_document(self, archive, filename, doc):
        doc = self._doc_preproc(doc)

        if len(doc):
            outputs = [[] for n in self.info.output_names]

            for chunk in doc:
                # Call CoreNLP on the chunk (sentence, paragraph)
                try:
                    json_result = self.corenlp.annotate(chunk.encode("utf-8"), self.properties)
                except CoreNLPProcessingError, e:
                    # TODO: do something other than re-raise
                    raise

                for output_num, output_name in enumerate(self.info.output_names):
                    if output_name == "annotations":
                        outputs[output_num].extend(
                            [
                                [
                                    [word_data[field_name] for field_name in self.output_fields]
                                    for word_data in sentence["tokens"]
                                ] for sentence in json_result["sentences"]
                            ]
                        )
                    elif output_name == "parse":
                        outputs[output_num].extend(
                            [sentence["parse"] for sentence in json_result["sentences"]]
                        )

            return tuple(outputs)
        else:
            # Return a None for every output
            return tuple([None] * len(self.info.output_names))

    def postprocess(self, error=False):
        self.corenlp.shutdown()
