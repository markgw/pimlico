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

    Datatypes are used to specify the routines for reading the output from modules. They're also
    used to specify how to read pipeline inputs. Most datatypes that have data simply read it in
    when required. Some (in particular those use as inputs) need a preparation phase to be run,
    where the raw data itself isn't sufficient to implement the reading interfaces required. In this
    case, they should override prepare_data().

    Datatypes may require/allow options to be set when they're used to read pipeline inputs. These
    are specified, in the same way as module options, by input_module_options on the datatype class.

    """
    datatype_name = "base_datatype"
    requires_data_preparation = False
    input_module_options = []

    def __init__(self, base_dir, **kwargs):
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data") if base_dir is not None else None
        self._metadata = None

        for attr, val in kwargs.items():
            setattr(self, attr, val)

    @property
    def metadata(self):
        if self._metadata is None:
            # Load dictionary of metadata
            with open(os.path.join(self.base_dir, "corpus_metadata"), "r") as f:
                self._metadata = pickle.load(f)
        return self._metadata

    def check_runtime_dependencies(self):
        """
        Like the similarly named method on executors, this check dependencies for using the datatype.
        It's not called when checking basic config, but only when the datatype is needed.

        Returns a list of pairs: (dependency short name, description/error message)

        """
        return []

    def prepare_data(self, log):
        return

    @classmethod
    def create_from_options(cls, base_dir, options={}):
        return cls(base_dir, **options)

    def data_ready(self):
        """
        Check whether the data corresponding to this datatype instance exists and is ready to be read.

        Default implementation just checks whether the data dir exists. Subclasses might want to add their own
        checks, or even override this, if the data dir isn't needed.

        """
        # If data_dir is None, the datatype doesn't need it
        return self.data_dir is None or os.path.exists(self.data_dir)


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
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(os.path.join(self.base_dir, "corpus_metadata"), "w") as f:
            pickle.dump(self.metadata, f, -1)


class IterableDocumentCorpus(PimlicoDatatype):
    """
    Superclass of all datatypes which represent a dataset that can be iterated over document by document.
    The actual type of the data depends on the subclass: it could be, e.g. coref output, etc.

    At creation time, length should be provided in the metadata, denoting how many documents are in the dataset.

    """
    datatype_name = "iterable_corpus"

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


def load_datatype(path):
    """
    Try loading a datatype class for a given path. Raises a DatatypeLoadError if it's not a valid
    datatype path.

    """
    mod_path, __, cls_name = path.rpartition(".")
    try:
        mod = import_module(mod_path)
    except ImportError:
        raise DatatypeLoadError("could not load module %s" % mod_path)

    if not hasattr(mod, cls_name):
        raise DatatypeLoadError("could not load datatype class %s in module %s" % (cls_name, mod_path))
    cls = getattr(mod, cls_name)

    if not issubclass(cls, PimlicoDatatype):
        raise DatatypeLoadError("%s is not a Pimlico datatype" % path)
    return cls
