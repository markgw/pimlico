"""
Input module for extracting documents from XML files. Gigaword, for example, is stored in this way.

Depends on BeautifulSoup (see "bs4" target in lib dir Makefile).

"""
import gzip
import os

from pimlico.core.modules.base import DependencyError
from pimlico.datatypes.base import IterableDocumentCorpus, PimlicoDatatypeWriter
from pimlico.utils.progress import get_progress_bar


class XmlDocumentIterator(IterableDocumentCorpus):
    requires_data_preparation = True
    input_module_options = [
        ("path", {
            "required": True,
            "help": "Path to the data",
        }),
        ("document_node_type", {
            "help": "XML node type to extract documents from (default: 'doc')",
            "default": "doc",
        }),
        ("document_name_attr", {
            "help": "Attribute of document nodes to get document name from (default: 'id')",
            "default": "id",
        })
    ]

    def __iter__(self):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise DependencyError("BeautifulSoup could not be found. Have you run the make target in the lib dir?")

        if not os.path.isdir(self.path):
            # Just a single file
            files = [(os.path.dirname(os.path.abspath(self.path)), os.path.basename(self.path))]
        else:
            # Directory: iterate over all files
            files = [
                (dirname, filename)
                for (dirname, dirs, filenames) in os.walk(self.path)
                for filename in filenames
            ]

        for dirname, filename in files:
            if filename.endswith(".gz"):
                # Permit gzip files by opening them using the gzip library
                with gzip.open(os.path.join(dirname, filename), "r") as f:
                    data = f.read()
            else:
                with open(os.path.join(dirname, filename), "r") as f:
                    data = f.read()

            # Read the XML using Beautiful Soup, so we can handle messy XML in a tolerant fashion
            soup = BeautifulSoup(data)

            # Look for the type of XML node that documents are stored in
            for doc_node in soup.find_all(self.document_node_type):
                # The node should supply us with the document name, using the attribute name specified
                doc_name = doc_node.get(self.document_name_attr)
                # Pull the text out of the document node
                doc_text = doc_node.text
                yield doc_name, doc_text

    def check_runtime_dependencies(self):
        missing_dependencies = []
        try:
            import bs4
        except ImportError:
            missing_dependencies.append(("BeautifulSoup", "install in Python lib dir using make"))
        missing_dependencies.extend(super(XmlDocumentIterator, self).check_runtime_dependencies())
        return missing_dependencies

    def prepare_data(self, log):
        from bs4 import BeautifulSoup

        # Count the number of documents in the corpus
        # Iterate over the corpus in a similar way to the datatype that reads documents, but just count the DOC tags

        if not os.path.isdir(self.path):
            # Just a single file
            files = [(os.path.dirname(os.path.abspath(self.path)), os.path.basename(self.path))]
        else:
            # Directory: iterate over all files
            files = [
                (dirname, filename)
                for (dirname, dirs, filenames) in os.walk(self.path)
                for filename in filenames
            ]
        log.info("Counting docs in %s files" % len(files))

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
            num_docs += len(soup.find_all(self.document_node_type))

        log.info("Counted %d docs" % num_docs)
        with PimlicoDatatypeWriter(self.base_dir) as datatype:
            datatype.metadata["length"] = num_docs

    def data_ready(self):
        # Check that the input path exists and that we've prepared the data to get the length
        return super(XmlDocumentIterator, self).data_ready() and \
               os.path.exists(self.path) and \
               "length" in self.metadata
