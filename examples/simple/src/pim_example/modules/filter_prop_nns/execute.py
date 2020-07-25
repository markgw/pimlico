import re

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory

initial_cap_re = re.compile(r"[A-Z]")


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # Apply the processing for each document here
    sentences = [
        # Always pass the first word through unmodified
        [sent[0]] +
        # Filter out any other words that start with a capital
        [word for word in sent[1:] if not initial_cap_re.match(word)]
        for sent in doc.sentences
    ]

    return dict(sentences=sentences)


ModuleExecutor = multiprocessing_executor_factory(process_document)
