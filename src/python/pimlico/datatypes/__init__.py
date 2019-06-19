from __future__ import absolute_import

# Import all builtin datatypes here so that we can easily access them as pimlico.datatypes.DatatypeName
from pimlico.utils.core import import_member
from .base import PimlicoDatatype, DynamicOutputDatatype, DynamicInputDatatypeRequirement, MultipleInputs, \
    DatatypeLoadError
from .core import StringList, Dict
from .files import NamedFileCollection, NamedFile, FilesInput, FileInput, TextFile
from .dictionary import Dictionary
from .embeddings import Embeddings, TSVVecFiles
from .gensim import GensimLdaModel
from .corpora.base import IterableCorpus
from .corpora.grouped import GroupedCorpus

# All builtin datatypes that may be easily loaded using their
# class names of datatype names from config files
BUILTIN_DATATYPES = [
    PimlicoDatatype, IterableCorpus, GroupedCorpus,
    StringList, Dict, NamedFileCollection, NamedFile, TextFile, Dictionary,
    Embeddings, TSVVecFiles, GensimLdaModel,
]
BUILTIN_DATATYPES_BY_DATATYPE_NAME = dict(
    # Go through them in reverse, so that, if we make a mistake and have a duplicate name, the
    # earlier ones take priority
    (datatype.datatype_name, datatype) for datatype in reversed(BUILTIN_DATATYPES)
)
BUILTIN_DATATYPES_BY_CLASS_NAME = dict(
    (datatype.__name__, datatype) for datatype in reversed(BUILTIN_DATATYPES)
)


def load_datatype(path, options={}):
    """
    Try loading a datatype class for a given path. Raises a DatatypeLoadError if it's not a valid
    datatype path. Also looks up class names of builtin datatypes and datatype names.

    Options are unprocessed strings that will be processed using the datatype's option
    definitions.

    """
    # Check whether the name is a class name or datatype name of a builtin datatype
    if path in BUILTIN_DATATYPES_BY_DATATYPE_NAME:
        cls = BUILTIN_DATATYPES_BY_DATATYPE_NAME[path]
    elif path in BUILTIN_DATATYPES_BY_CLASS_NAME:
        cls = BUILTIN_DATATYPES_BY_CLASS_NAME[path]
    else:
        try:
            cls = import_member(path)
        except ImportError as e:
            raise DatatypeLoadError("could not load datatype class %s: %s" % (path, e))

    # The type of the class will generally not be "type", since we use meta classes
    # However, it should be a subclass of it
    # This distinguishes it from, e.g. modules
    if not issubclass(type(cls), type(object)):
        raise DatatypeLoadError("tried to load datatype %s, but result was not a class, it was a %s" %
                                (path, type(cls).__name__))

    if not issubclass(cls, PimlicoDatatype):
        raise DatatypeLoadError("%s is not a Pimlico datatype" % path)

    # Instantiate the datatype, taking account of (unprocessed) options
    dt = cls.instantiate_from_options(options)

    return dt
