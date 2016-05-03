import os
import tempfile

from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from py4j.java_collections import ListConverter


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    # Reformat the docs so we have each parse tree on one line
    doc = [u" ".join(line for line in sentence.splitlines()) for sentence in doc]
    doc = [sent.encode("utf-8") for sent in doc]
    # Convert to a Java list
    doc = ListConverter().convert(doc, worker._gateway._gateway_client)
    # TODO Call is now working. Error in reading input strings -- version problem with CoreNLP?
    return [
        [token.split("\t") for token in sentence]
        for sentence in worker._gateway.entry_point.markupParsedDocument(filename, doc)
    ]


def preprocess(executor):
    # Create an XML file that Caevo can use to load WordNet
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as xml_file:
        with open(executor.info.template_jwnl_path, "r") as template_file:
            xml_file.write(template_file.read().replace("%%WORDNET_DIR%%", executor.info.wordnet_dir))
    executor.jwnl_path = xml_file.name
    try:
        # Initialize the Malt Py4J gateway
        executor.interface = Py4JInterface("pimlico.caevo.CaevoGateway", gateway_args=[executor.info.sieves_path],
                                           pipeline=executor.info.pipeline,
                                           # Set the path to the wordnet dicts as an environment variable
                                           env={"JWNL": executor.jwnl_path})
        executor.interface.start(port_output_prefix="PORT: ")
    except:
        # If anything goes wrong, remove the temporary file
        os.remove(executor.jwnl_path)
        raise


def postprocess(executor, error=False):
    # Close down the Py4J gateway
    executor.interface.stop()
    # Get rid of the temporary file we used to store wordnet settings
    os.remove(executor.jwnl_path)


def worker_set_up(worker):
    # Create a gateway to the single py4j server, which should already be running
    worker._gateway = gateway_client_to_running_server(worker.executor.interface.port_used)


def worker_tear_down(worker):
    worker._gateway.close()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    preprocess_fn=preprocess, postprocess_fn=postprocess,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
)
