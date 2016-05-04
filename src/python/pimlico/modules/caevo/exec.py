import os
import tempfile

from pimlico import JAVA_LIB_DIR
from pimlico.core.external.java import Py4JInterface
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
    doc = ListConverter().convert(doc, worker.interface.gateway._gateway_client)
    # Call Caevo
    result = worker.interface.gateway.entry_point.markupParsedDocument(filename, doc)
    # JDOM uses Windows-style double carriage returns
    # Change to \ns, to be consistent with what we normally do
    result = "\n".join(result.splitlines())
    return result


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
        prefix_classpath=os.path.join(JAVA_LIB_DIR, "caevo-1.1-jar-with-dependencies.jar")
    )
    worker.interface.start(port_output_prefix="PORT: ")


def worker_tear_down(worker):
    # Close down the Py4J gateway
    worker.interface.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    preprocess_fn=preprocess, postprocess_fn=postprocess,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
)
