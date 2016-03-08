"""
Input module for extracting documents from XML files. Gigaword, for example, is stored in this way.

Depends on BeautifulSoup (see "bs4" target in lib dir Makefile).

"""
import gzip
import os
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.inputs import InputModuleInfo
from pimlico.datatypes.base import IterableDocumentCorpus


class XmlDocumentIterator(IterableDocumentCorpus):
    def __init__(self, input_path, document_node_type="doc", document_name_attr="id"):
        # Pass the input path up to the super constructor as the base dir
        super(XmlDocumentIterator, self).__init__(input_path)
        self.document_name_attr = document_name_attr
        self.document_node_type = document_node_type
        self.input_path = input_path

    def __iter__(self):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise DependencyError("BeautifulSoup could not be found. Have you run the make target in the lib dir?")

        if not os.path.isdir(self.input_path):
            # Just a single file
            files = [(os.path.dirname(os.path.abspath(self.input_path)), os.path.basename(self.input_path))]
        else:
            # Directory: iterate over all files
            files = (
                (dirname, filename)
                for (dirname, dirs, filenames) in os.walk(self.input_path)
                for filename in filenames
            )

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


class ModuleInfo(InputModuleInfo):
    module_type_name = "xml_extract"
    module_outputs = [("documents", XmlDocumentIterator)]
    module_options = [
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

    def instantiate_output_datatype(self, output_name, output_datatype):
        # Datatype is always XmlDocumentIterator
        return output_datatype(self.options["path"],
                               self.options["document_node_type"],
                               self.options["document_name_attr"])
