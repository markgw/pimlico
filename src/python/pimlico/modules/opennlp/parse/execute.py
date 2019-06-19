# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Each process starts up a separate JVM to make calls to the coref gateway.

This may seem an unnecessary use of memory, etc, since Py4J is thread-safe and manages connections so that
we can make multiple asynchronous calls to the same gateway. However, OpenNLP is not thread-safe, so things
grind to a halt if we do this.

"""
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.old_datatypes import TokenizedCorpus

from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from py4j.java_collections import ListConverter


def process_document(worker, archive, filename, doc):
    """
    Common document processing routine used by parallel and non-parallel versions.

    """
    doc = worker.info._preprocess_doc(doc)
    # Input is a raw string: split on newlines to get tokenized sentences
    sentences = doc.splitlines()
    sentence_list = ListConverter().convert(sentences, worker.interface.gateway._gateway_client)
    # Parse
    return list(worker.interface.gateway.entry_point.parseTrees(sentence_list))


def start_interface(info):
    """
    Start up a Py4J interface to a new JVM.

    """
    # Start a parser process running in the background via Py4J
    interface = Py4JInterface(
        "pimlico.opennlp.ParserGateway", gateway_args=[info.model_path], pipeline=info.pipeline,
        # Parser tool outputs warnings to stderr if parsing fails: we really don't need to know about every problem
        print_stderr=False, print_stdout=False
    )
    try:
        interface.start()
    except JavaProcessError as e:
        raise ModuleExecutionError("error starting parser process: %s" % e)
    return interface


def worker_set_up(worker):
    worker.interface = start_interface(worker.info)


def worker_tear_down(worker):
    worker.interface.stop()


def preprocess(executor):
    if isinstance(executor.input_corpora[0], TokenizedCorpus):
        executor.input_corpora[0].raw_data = True


ModuleExecutor = multiprocessing_executor_factory(
    process_document, preprocess_fn=preprocess, worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down
)
