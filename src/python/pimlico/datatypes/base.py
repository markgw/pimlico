"""
Datatypes provide interfaces for reading (and in some cases writing) datasets. At their most basic,
they define a way to iterate over a dataset linearly. Some datatypes may also provide other functionality,
such as random access or compression.

As much as possible, Pimlico pipelines should use standard datatypes to connect up the output of modules
with the input of others. Most datatypes have a lot in common, which should be reflected in their sharing
common base classes. Custom datatypes will be needed for most datasets when they're used as inputs, but
as far as possible, these should be converted into standard datatypes, or at least a form where they can
use standard idioms for iterating, etc, early in the pipeline.

"""
from importlib import import_module
import os
import cPickle as pickle


class PimlicoDatatype(object):
    """
    The abstract superclass of all datatypes. Provides basic functionality for identifying where
    data should be stored and such.

    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data")

        # Load dictionary of metadata
        with open(os.path.join(self.base_dir, "corpus_metadata"), "r") as f:
            self.metadata = pickle.load(f)

    def check_runtime_dependencies(self):
        """
        Like the similarly named method on executors, this check dependencies for using the datatype.
        It's not called when checking basic config, but only when the datatype is needed.

        Returns a list of pairs: (dependency short name, description/error message)

        """
        return []


class PimlicoDatatypeWriter(object):
    """
    Abstract base class fo data writer associated with Pimlico datatypes.

    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata = {}

    def __enter__(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(os.path.join(self.base_dir, "corpus_metadata"), "w") as f:
            pickle.dump(self.metadata, f, -1)


class IterableDocumentCorpus(PimlicoDatatype):
    """
    Superclass of all datatypes which represent a dataset that can be iterated over document by document.
    The actual type of the data depends on the subclass: it could be, e.g. coref output, etc.

    At creation time, length should be provided in the metadata, denoting how many documents are in the dataset.

    """
    def __init__(self, *args, **kwargs):
        super(IterableDocumentCorpus, self).__init__(*args, **kwargs)

    def __iter__(self):
        """
        Subclasses should implement an iter method that simply iterates over all the documents in the
        corpus in a consistent order. They may also provide other methods for iterating over or otherwise
        accessing the data.

        """
        raise NotImplementedError

    def __len__(self):
        return self.metadata["length"]


class IterableDocumentCorpusWriter(PimlicoDatatypeWriter):
    def __exit__(self, exc_type, exc_val, exc_tb):
        super(IterableDocumentCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)
        # Check the length has been set
        if "length" not in self.metadata:
            raise DatatypeWriteError("writer for IterableDocumentCorpus must set a 'length' value in the metadata")


class DatatypeLoadError(Exception):
    pass


class DatatypeWriteError(Exception):
    pass
