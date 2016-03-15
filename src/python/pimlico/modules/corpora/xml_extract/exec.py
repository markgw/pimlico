from bs4 import BeautifulSoup
import gzip
import os
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import PimlicoDatatypeWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self, module_instance_info):
        # Count the number of documents in the corpus
        # Iterate over the corpus in a similar way to the datatype that reads documents, but just count the DOC tags
        input_path = module_instance_info.options["path"]

        if not os.path.isdir(input_path):
            # Just a single file
            files = [(os.path.dirname(os.path.abspath(input_path)), os.path.basename(input_path))]
        else:
            # Directory: iterate over all files
            files = (
                (dirname, filename)
                for (dirname, dirs, filenames) in os.walk(input_path)
                for filename in filenames
            )

        num_docs = 0
        pbar = get_progress_bar(len(files), title="Counting documents")
        for dirname, filename in pbar(files):
            if filename.endswith(".gz"):
                # Permit gzip files by opening them using the gzip library
                with gzip.open(os.path.join(dirname, filename), "r") as f:
                    data = f.read()
            else:
                with open(os.path.join(dirname, filename), "r") as f:
                    data = f.read()

            # Read the XML using Beautiful Soup, so we can handle messy XML in a tolerant fashion
            soup = BeautifulSoup(data)
            # Look for the type of XML node that documents are stored in and count them
            num_docs += len(soup.find_all(module_instance_info.options["document_node_type"]))

        with PimlicoDatatypeWriter(module_instance_info.get_output_dir()) as datatype:
            datatype.metadata["length"] = num_docs