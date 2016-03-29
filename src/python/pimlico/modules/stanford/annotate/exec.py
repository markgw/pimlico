import os
from pimlico import JAVA_LIB_DIR
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor
from stanford_corenlp_pywrapper import CoreNLP
from pimlico.datatypes.tar import TarredCorpus
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


def _word_annotation_preproc(doc):
    return "\n".join(
        " ".join(word["word"] for word in sentence)
        for sentence in doc
    )


class ModuleExecutor(DocumentMapModuleExecutor):
    def get_writer(self, info):
        output_datatype = info.get_output("documents")
        return SimpleWordAnnotationCorpusWriter(info.get_output_dir("documents"),
                                                output_datatype.read_annotation_fields())

    def preprocess(self, info):
        annotators = []
        if type(self.input_corpora[0]) is TarredCorpus:
            # Data not already run through a tokenizer: include tokenization and sentence splitting
            annotators.extend(["tokenize", "ssplit"])
        annotators.extend(info.options["annotators"].split(","))

        # Prepare a CoreNLP background process to do the processing
        self.corenlp = CoreNLP(
            configdict={"annotators": annotators},
            output_types=[annotators],
            corenlp_jars=[os.path.join(JAVA_LIB_DIR, "*")]
        )

        # By default, for a TarredCorpus or TokenizedCorpus, just pass in the document text
        self._doc_preproc = lambda doc: doc
        if type(self.input_corpora[0]) is TokenizedCorpus:
            # Just get the raw text data, which we happen to know is tokenized
            self.input_corpora[0].raw_data = True
        elif isinstance(self.input_corpora[0], WordAnnotationCorpus):
            # For a word annotation corpus, we need to pull out the words
            self._doc_preproc = _word_annotation_preproc

    def process_document(self, archive, filename, doc):
        doc = self._doc_preproc(doc)
        # Call CoreNLP on the doc
        # TODO Not working -- not sure why
        json_result = self.corenlp.parse_doc(doc.encode("utf-8"))
        print json_result
        # TODO Do something with the result
        # Output one sentence per line
        #return u"\n".join(tokenized_sents)

    def postprocess(self, info, error=False):
        pass
