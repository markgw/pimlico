# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os
import tempfile
from py4j.java_collections import ListConverter

from pimlico import JAVA_LIB_DIR
from pimlico.core.external.java import Py4JInterface, make_py4j_errors_safe
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error, skip_invalids
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


# Used to do it this way
# @skip_invalid
# @invalid_doc_on_error
# @make_py4j_errors_safe
# def process_document(worker, archive, filename, doc):
#     # Call Caevo
#     result = worker.interface.gateway.entry_point.markupRawText(filename, doc.encode("utf-8"))
#     # JDOM uses Windows-style double carriage returns
#     # Change to \ns, to be consistent with what we normally do
#     result = u"\n".join(result.splitlines())
#     worker.interface.clear_output_queues()
#     return result


@skip_invalids
@make_py4j_errors_safe
def process_documents(worker, input_tuples):
    # Take a load of docs in one go to speed things up
    filenames = [doc_tuple[1] for doc_tuple in input_tuples]
    docs = [doc_tuple[2].encode("utf-8") for doc_tuple in input_tuples]
    # Make into Java lists
    filenames = ListConverter().convert(filenames, worker.interface.gateway._gateway_client)
    docs = ListConverter().convert(docs, worker.interface.gateway._gateway_client)

    # Call Caevo
    results = worker.interface.gateway.entry_point.markupRawTexts(filenames, docs)
    # JDOM uses Windows-style double carriage returns
    # Change to \ns, to be consistent with what we normally do
    results = [u"\n".join(result.splitlines()) for result in results]
    worker.interface.clear_output_queues()
    return results


def preprocess(executor):
    # Create an XML file that Caevo can use to load WordNet
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as xml_file:
        with open(executor.info.template_jwnl_path, "r") as template_file:
            xml_file.write(template_file.read().replace("%%WORDNET_DIR%%", executor.info.wordnet_dir))
    executor.jwnl_path = xml_file.name


def postprocess(executor, error=False):
    # Get rid of the temporary file we used to store wordnet settings
    os.remove(executor.jwnl_path)


def worker_set_up(worker):
    # Initialize the Malt Py4J gateway
    worker.interface = Py4JInterface(
        "pimlico.caevo.CaevoGateway", gateway_args=[worker.info.sieves_path],
        pipeline=worker.info.pipeline,
        # Set the path to the wordnet dicts as an environment variable
        env={"JWNL": worker.executor.jwnl_path},
        # Put the Caevo dependencies at front of classpath, to make sure they take precedence over other versions
        prefix_classpath=os.path.join(JAVA_LIB_DIR, "caevo-1.1-jar-with-dependencies.jar"),
        print_stderr=False, print_stdout=False,
        # Try to bleed everything we can out of Java, as Caevo is very slow
        java_opts=[
            # Makes startup slower, but execution faster
            "-server",
            # Enables aggressive optimization, which might make it faster
            "-XX:+AggressiveOpts",
            # Parallel garbage collection: seems to speed things up a bit
            "-XX:+UseParallelGC"
        ],
    )
    worker.interface.start(port_output_prefix="PORT: ")


def worker_tear_down(worker):
    # Close down the Py4J gateway
    worker.interface.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_documents,
    preprocess_fn=preprocess, postprocess_fn=postprocess,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
    # Try to speed things up by giving Caevo multiple docs at once to process
    batch_docs=20
)
