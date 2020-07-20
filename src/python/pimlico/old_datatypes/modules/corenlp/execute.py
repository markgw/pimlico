# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Uses the threaded, rather than multiproc, implementations of document map processors, since the main work
of this executor is done by the CoreNLP server. We simply fire of requested from python threads and each one
gets a new Java thread in the server.

"""
from traceback import format_exc

from pimlico.core.dependencies.java import get_module_classpath
from pimlico.core.modules.execute import StopProcessing
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.threaded import threading_executor_factory
from pimlico.old_datatypes.base import InvalidDocument
from pimlico.old_datatypes.parse.dependency import StanfordDependencyParse
from pimlico.old_datatypes.tokenized import TokenizedCorpus, TokenizedDocumentType
from pimlico.old_datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationsDocumentType
from pimlico.old_datatypes.modules.corenlp import CoreNLPProcessingError
from pimlico.old_datatypes.modules.corenlp import CoreNLP


def preprocess(executor):
    annotators = []
    # TODO Work out how to pass in annotations already done if they're given
    if not isinstance(executor.input_corpora[0], (WordAnnotationCorpus, TokenizedCorpus)):
        # Data not already run through a tokenizer: include tokenization and sentence splitting
        annotators.extend(["tokenize", "ssplit"])
    annotators.extend(executor.info.options["annotators"].split(",") if executor.info.options["annotators"] else [])
    # Leave out "word": allowed as annotator setting to do tokenization, but shouldn't be passed through to CoreNLP
    if "word" in annotators:
        annotators.remove("word")

    if "parse" in executor.info.output_names or "parse-deps" in executor.info.output_names:
        # We need the parser to be run. CoreNLP will automatically add POS tagger if necessary
        annotators.append("parse")
    if "dep-parse" in executor.info.output_names:
        # Include the dep parser in processing
        annotators.append("depparse")
    if "coref" in executor.info.output_names:
        # Include coref resolution
        annotators.append("coref")
    executor.dep_output_type = "%s-dependencies" % executor.info.options["dep_type"]

    # By default, for a TarredCorpus or TokenizedCorpus, just pass in the document text
    executor._doc_preproc = lambda doc: doc
    if isinstance(executor.input_corpora[0].data_point_type, WordAnnotationsDocumentType):
        # For a word annotation corpus, we need to pull out the words
        executor._doc_preproc = lambda doc: "\n".join(" ".join(word["word"] for word in sentence) for sentence in doc)
    elif isinstance(executor.input_corpora[0].data_point_type, TokenizedDocumentType):
        # Just get the raw text data, which we happen to know is tokenized
        executor.input_corpora[0].raw_data = True

    # Prepare the list of attributes to extract from the output and send to the writer
    if "annotations" in executor.info.output_names:
        executor.output_fields = executor.info.get_output_datatype("annotations")[1].annotation_fields
    else:
        executor.output_fields = None

    # Prepare a CoreNLP background process to do the processing
    executor.corenlp = CoreNLP(executor.info.pipeline, executor.info.options["timeout"],
                               classpath=get_module_classpath(executor.info))
    executor.corenlp.start()
    executor.log.info("CoreNLP server started on %s" % executor.corenlp.server_url)
    executor.log.info("Calling CoreNLP with annotators: %s" % ", ".join(annotators))
    executor.log.info("Annotations that will be available on the output: %s" % ", ".join(
        executor.info.get_output_datatype("annotations")[1].annotation_fields
    ))
    executor.properties = {
        "annotators": ",".join(annotators),
        "outputFormat": "json",
    }


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    doc = worker.executor._doc_preproc(doc)

    if len(doc):
        # Call CoreNLP on the chunk (sentence, paragraph)
        try:
            json_result = worker.executor.corenlp.annotate(doc.encode("utf-8"), worker.executor.properties)
        except CoreNLPProcessingError as e:
            # Error while processing the input from the document
            # Output an invalid document, with some error information
            return InvalidDocument(worker.info.module_name, "CoreNLP processing error: %s\n%s" %
                                   (e, format_exc()))

        # Prepare output data for each of the output writers
        outputs = []
        for output_num, output_name in enumerate(worker.info.output_names):
            if output_name == "annotations":
                # Pull out all of the required annotation fields for each word
                outputs.append([
                    [
                        [word_data[field_name] for field_name in worker.executor.output_fields]
                        for word_data in sentence["tokens"]
                    ] for sentence in json_result["sentences"]
                ])
            elif output_name == "parse":
                outputs.append([sentence["parse"] for sentence in json_result["sentences"]])
            elif output_name in ["parse-deps", "dep-parse"]:
                outputs.append([
                    StanfordDependencyParse.from_json(sentence[worker.executor.dep_output_type])
                    for sentence in json_result["sentences"]
                ])
            elif output_name == "raw":
                outputs.append(json_result)
            elif output_name == "coref":
                outputs.append(json_result["corefs"])
            elif output_name == "tokenized":
                outputs.append([
                    [word_data["word"] for word_data in sentence["tokens"]] for sentence in json_result["sentences"]
                ])
            else:
                raise StopProcessing("unknown output name in output list: %s" % output_name)

        return tuple(outputs)
    else:
        # Return a None for every output
        return tuple([None] * len(worker.info.output_names))


def postprocess(executor, error=False):
    executor.corenlp.shutdown()


ModuleExecutor = threading_executor_factory(process_document, preprocess_fn=preprocess, postprocess_fn=postprocess)
