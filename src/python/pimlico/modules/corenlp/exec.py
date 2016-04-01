import Queue
from threading import Thread
from traceback import format_exc

from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, DocumentProcessorPool, ProcessOutput
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.jsondoc import JsonDocumentCorpusWriter
from pimlico.datatypes.parse import ConstituencyParseTreeCorpusWriter, StanfordDependencyParse, \
    DependencyParseCorpusWriter
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from pimlico.modules.corenlp import CoreNLPProcessingError
from pimlico.modules.corenlp.wrapper import CoreNLP
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


class CoreNLPPool(DocumentProcessorPool):
    """
    Simple pool for sending off multiple calls to the CoreNLP server at once. It doesn't use multiprocessing --
    that's actually provided by the server. It just uses threading to send non-blocking requests to the server
    and let it take its time over every job.

    """
    def __init__(self, executor, processes):
        super(CoreNLPPool, self).__init__(processes)
        self.executor = executor

    @staticmethod
    def create_queue():
        # Don't need a multiprocessing queue, since we only use threading
        return Queue.Queue()

    def process_document(self, archive, filename, doc):
        # The real work is done by the CoreNLP server, so we just make the call from within this thread
        # The thread will spend most of its time just waiting for the result
        def _doc_process_async():
            # Call the usual processing function
            result = self.executor.process_document(archive, filename, doc)
            # Put the result onto the queue
            self.queue.put(ProcessOutput(archive, filename, result))
        t = Thread(target=_doc_process_async)
        t.daemon = True
        # Set the thread going and leave it to its own devices
        t.start()


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def get_writer(self, output_name):
        output_dir = self.info.get_output_dir(output_name)
        gzip = self.info.options["gzip"]
        readable = self.info.options["readable"]
        if output_name == "annotations":
            output_name, output_datatype = self.info.get_output_datatype(output_name)
            return SimpleWordAnnotationCorpusWriter(output_dir, output_datatype.annotation_fields)
        elif output_name == "parse":
            # Just write out parse trees as they come from the parser
            return ConstituencyParseTreeCorpusWriter(output_dir, gzip=gzip)
        elif output_name == "parse-deps":
            return DependencyParseCorpusWriter(output_dir, gzip=gzip, readable=readable)
        elif output_name == "dep-parse":
            return DependencyParseCorpusWriter(output_dir, gzip=gzip, readable=readable)
        elif output_name == "raw":
            return JsonDocumentCorpusWriter(output_dir, gzip=gzip, readable=readable)
        elif output_name == "coref":
            return JsonDocumentCorpusWriter(output_dir, gzip=gzip, readable=readable)
        else:
            raise ValueError("unknown output '%s'" % output_name)

    def preprocess(self):
        annotators = []
        # TODO Work out how to pass in annotations already done if they're given
        if not isinstance(self.input_corpora[0], (WordAnnotationCorpus, TokenizedCorpus)):
            # Data not already run through a tokenizer: include tokenization and sentence splitting
            annotators.extend(["tokenize", "ssplit"])
        annotators.extend(self.info.options["annotators"].split(",") if self.info.options["annotators"] else [])
        # Leave out "word": allowed as annotator setting to do tokenization, but shouldn't be passed through to CoreNLP
        if "word" in annotators:
            annotators.remove("word")

        if "parse" in self.info.output_names or "parse-deps" in self.info.output_names:
            # We need the parser to be run. CoreNLP will automatically add POS tagger if necessary
            annotators.append("parse")
        if "dep-parse" in self.info.output_names:
            # Include the dep parser in processing
            annotators.append("depparse")
        if "coref" in self.info.output_names:
            # Include coref resolution
            annotators.append("coref")
        self.dep_output_type = "%s-dependencies" % self.info.options["dep_type"]

        # By default, for a TarredCorpus or TokenizedCorpus, just pass in the document text
        self._doc_preproc = lambda doc: doc
        if isinstance(self.input_corpora[0], WordAnnotationCorpus):
            # For a word annotation corpus, we need to pull out the words
            self._doc_preproc = lambda doc: "\n".join(" ".join(word["word"] for word in sentence) for sentence in doc)
        elif isinstance(self.input_corpora[0], TokenizedCorpus):
            # Just get the raw text data, which we happen to know is tokenized
            self.input_corpora[0].raw_data = True

        # Prepare the list of attributes to extract from the output and send to the writer
        if "annotations" in self.info.output_names:
            self.output_fields = self.info.get_output_datatype("annotations")[1].annotation_fields
        else:
            self.output_fields = None

        # Prepare a CoreNLP background process to do the processing
        self.corenlp = CoreNLP(self.info.pipeline, self.info.options["timeout"])
        self.corenlp.start()
        self.log.info("CoreNLP server started on %s" % self.corenlp.server_url)
        self.log.info("Calling CoreNLP with annotators: %s" % ", ".join(annotators))
        self.properties = {
            "annotators": ",".join(annotators),
            "outputFormat": "json",
        }

    def create_pool(self, processes):
        # CoreNLP server has already been set going by preprocess()
        return CoreNLPPool(self, processes)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, doc):
        doc = self._doc_preproc(doc)

        if len(doc):
            # Call CoreNLP on the chunk (sentence, paragraph)
            try:
                json_result = self.corenlp.annotate(doc.encode("utf-8"), self.properties)
            except CoreNLPProcessingError, e:
                # Error while processing the input from the document
                # Output an invalid document, with some error information
                return InvalidDocument(self.info.module_name, "CoreNLP processing error: %s\n%s" %
                                       (e, format_exc()))

            # Prepare output data for each of the output writers
            outputs = []
            for output_num, output_name in enumerate(self.info.output_names):
                if output_name == "annotations":
                    # Pull out all of the required annotation fields for each word
                    outputs.append([
                        [
                            [word_data[field_name] for field_name in self.output_fields]
                            for word_data in sentence["tokens"]
                        ] for sentence in json_result["sentences"]
                    ])
                elif output_name == "parse":
                    outputs.append([sentence["parse"] for sentence in json_result["sentences"]])
                elif output_name in ["parse-deps", "dep-parse"]:
                    outputs.append([
                        StanfordDependencyParse.from_json(sentence[self.dep_output_type])
                        for sentence in json_result["sentences"]
                    ])
                elif output_name == "raw":
                    outputs.append(json_result)
                elif output_name == "coref":
                    outputs.append(json_result["corefs"])

            return tuple(outputs)
        else:
            # Return a None for every output
            return tuple([None] * len(self.info.output_names))

    def postprocess(self, error=False):
        self.corenlp.shutdown()
