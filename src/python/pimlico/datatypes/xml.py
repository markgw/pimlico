"""
Input module for extracting documents from XML files. Gigaword, for example, is stored in this way.

Depends on BeautifulSoup (see "bs4" target in lib dir Makefile).

"""
import gzip
import os
from multiprocessing import Pool, Queue

import time

from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.execute import ModuleExecutionError
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
        }),
        ("truncate", {
            "help": "Stop reading once we've got this number of documents",
            "type": int,
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

        n_docs = 0
        try:
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

                    n_docs += 1
                    if self.truncate is not None and n_docs >= self.truncate:
                        raise TruncateNow()
        except TruncateNow:
            pass

    def check_runtime_dependencies(self):
        missing_dependencies = []
        try:
            import bs4
        except ImportError:
            missing_dependencies.append(("BeautifulSoup", "install in Python lib dir using make"))
        missing_dependencies.extend(super(XmlDocumentIterator, self).check_runtime_dependencies())
        return missing_dependencies

    def prepare_data(self, log):
        # Count the number of documents in the corpus
        # Iterate over the corpus in a similar way to the datatype that reads documents, but just count the DOC tags

        if not os.path.isdir(self.path):
            # Just a single file
            files = [os.path.abspath(self.path)]
        else:
            # Directory: iterate over all files
            files = [
                os.path.join(dirname, filename)
                for (dirname, dirs, filenames) in os.walk(os.path.abspath(self.path))
                for filename in filenames
            ]
        if self.pipeline.processes > 1:
            processes_message = ", using %d parallel processes" % self.pipeline.processes
        else:
            processes_message = ""
        log.info("Counting docs in %s files%s" % (len(files), processes_message))

        num_docs = count_files_parallel(files, self.truncate, self.document_node_type, self.pipeline.processes)
        log.info("Counted %d docs" % num_docs)
        with PimlicoDatatypeWriter(self.base_dir) as datatype:
            datatype.metadata["length"] = num_docs

    def data_ready(self):
        # Check that the input path exists and that we've prepared the data to get the length
        return super(XmlDocumentIterator, self).data_ready() and \
               os.path.exists(self.path) and \
               "length" in self.metadata


def count_files_parallel(filenames, truncate, document_node_type, processes):
    num_docs = 0
    if truncate is not None:
        # Truncating, so update pbar with num docs and stop after we've got enough
        pbar = get_progress_bar(truncate, title="Counting documents")
    else:
        # Otherwise, don't know how many docs there are (that's the whole point) so count input files
        pbar = get_progress_bar(len(filenames), title="Counting documents")

    pool = Pool(processes=processes)
    jobs = []
    for filename in filenames:
        # Set a job going to count the docs in this file
        jobs.append(pool.apply_async(count_files_process, args=(filename, document_node_type)))
    pool.close()

    count = counted_files = 0
    # Wait for results to come through
    while counted_files < len(filenames):
        # Wait a bit and check again
        time.sleep(1.)

        completed_jobs = []
        for job in jobs:
            if job.ready():
                # This will raise any except that occurred in the process
                new_count = job.get()
                # Stop checking this job now
                completed_jobs.append(job)

                # Update our counts
                counted_files += 1
                count += new_count

                if truncate is not None:
                    if num_docs >= truncate:
                        # We've got at least as many docs as requested, so we'll stop after that number when iterating
                        pbar.finish()
                        # Stop all workers
                        pool.terminate()
                        return truncate
                    else:
                        pbar.update(count)
                else:
                    pbar.update(counted_files)

        # Stop checking on the completed jobs
        for job in completed_jobs:
            jobs.remove(job)
    pbar.finish()
    # Double-check that everything's finished
    pool.join()
    return count


def count_files_process(filename, document_node_type):
    from bs4 import BeautifulSoup

    if filename.endswith(".gz"):
        # Permit gzip files by opening them using the gzip library
        with gzip.open(filename, "r") as f:
            data = f.read()
    else:
        with open(filename, "r") as f:
            data = f.read()

    # Read the XML using Beautiful Soup, so we can handle messy XML in a tolerant fashion
    soup = BeautifulSoup(data)
    # Look for the type of XML node that documents are stored in and count them
    num_docs = len(soup.find_all(document_node_type))
    return num_docs


class TruncateNow(StopIteration):
    pass
