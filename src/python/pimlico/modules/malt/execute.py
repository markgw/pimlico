# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    # Prepare the input in the right format
    parser_input = "\n\n".join(
        worker.conll_format(sentence) for sentence in doc.word_annotations
    )
    # TODO Check working and remove prints
    print(parser_input)
    parser_output = worker._gateway.entry_point.parseDocFromCoNLLString(parser_input)
    print(parser_output)

    return {
        "word_annotations": [
            [worker.word_annotations_from_conll(token.split("\t"), input_annotations)
             for token, input_annotations in zip(output_sentence, input_sentence)]
            for input_sentence, output_sentence in zip(doc.word_annotations, parser_output)
        ]
    }


def preprocess(executor):
    # Initialize the Malt Py4J gateway
    executor.interface = Py4JInterface("pimlico.malt.ParserGateway", gateway_args=[executor.info.model_path],
                                       pipeline=executor.info.pipeline)
    executor.interface.start()


def postprocess(executor, error=False):
    # Close down the Py4J gateway
    executor.interface.stop()


def worker_set_up(worker):
    # Create a gateway to the single py4j server, which should already be running
    worker._gateway = gateway_client_to_running_server(worker.executor.interface.port_used)

    input_dt = worker.info.get_input_datatype("documents")
    output_dt = worker.info.get_output_datatype("parsed")
    # Prepare a function to convert the word-annotated input to CoNLL-X format
    # Input columns are: ID, form (word), lemma, C-POS, POS, feats, head, deprel, phead, pdeprel
    # We always need 'word' and 'pos' inputs
    # Lemma will be used if it is supplied in the input fields
    input_indices = [
        input_dt.field_pos["word"],
        input_dt.field_pos.get("lemma", None),
        input_dt.field_pos["pos"],
        None, None, None, None, None, None
    ]
    # Define a function to convert each sentence's word-annotation data into CoNLL format
    def _conll_format(sentence):
        return "\n".join(
            "{}\t{}".format(
                word_id,
                "\t".join(word_fields[field] if field is not None else "_"
                          for field in input_indices)
            ) for (word_id, word_fields) in enumerate(sentence)
        )
    worker.conll_format = staticmethod(_conll_format)
    # Keep a note of which fields should be passed through as they are and where they go in the output
    # This includes word, pos and possibly lemma
    pass_through_fields = dict(
        (output_dt.field_pos(input_field), input_field)
        for input_field in input_dt.fields
    )
    worker.pass_through_fields = pass_through_fields
    # Also define a mapping for the output from the parser to output annotation fields
    parser_output_fields = {
        output_dt.field_pos["feats"]: 5,
        output_dt.field_pos["head"]: 6,
        output_dt.field_pos["deprel"]: 7,
        output_dt.field_pos["phead"]: 8,
        output_dt.field_pos["pdeprel"]: 9,
    }
    # Check that all output fields can be retrieved either from the parser output or the input
    for i, field_name in enumerate(output_dt.fields):
        if i not in pass_through_fields and i not in parser_output_fields:
            raise ModuleExecutionError("per-word output field '{}' is neither being passed through directly "
                                       "from the input or retrieved from the parser output".format(field_name))

    def _word_annotations_from_conll(conll_fields, input_fields):
        return [parser_output_fields.get(i, pass_through_fields.get(i)) for i in range(len(output_dt.fields))]
    worker.word_annotations_from_conll = staticmethod(_word_annotations_from_conll)


def worker_tear_down(worker):
    worker._gateway.close()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    preprocess_fn=preprocess,
    postprocess_fn=postprocess
)
