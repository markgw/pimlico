from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    return [
        [
            [
                token_num,
                token["word"],
                # If lemmas aren't available, just repeat the word
                token.get("lemma", token["word"]),
                # If a special cpos field is supplied, use it, otherwise repeat the POS
                token.get("cpos", token["pos"]),
                # POS field is required
                token["pos"],
                # No word features
                None
            ]
            for token_num, token in enumerate(sentence, start=1)
        ] for sentence in doc
    ]


ModuleExecutor = multiprocessing_executor_factory(process_document)
