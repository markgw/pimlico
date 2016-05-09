from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    # Document is a CaevoDocument, where each entry is a sentence
    # Prepare output data for each of the output writers
    outputs = []
    for output_name in worker.info.output_names:
        if output_name == "tokenized":
            # The Caevo tokenization output is stored as a list of triples, where the word is the middle item of each
            outputs.append([[token[1] for token in entry.tokens] for entry in doc.entries])

    return tuple(outputs)


ModuleExecutor = multiprocessing_executor_factory(process_document)
