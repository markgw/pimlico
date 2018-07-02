# Import datatypes here to make it easier to specify their paths in config files
import warnings

from . import arrays
from . import base
from . import caevo
from . import coref
from . import dictionary
from . import documents
from . import features
from . import jsondoc
from . import parse
from . import tar
from . import tokenized
from . import word_annotations
from . import xml
from .arrays import *
from .base import *
from .caevo import *
from .coref import *
from .dictionary import *
from .documents import *
from .features import *
from .jsondoc import *
from .parse import *
from .tar import *
from .tokenized import *
from .word_annotations import *
from .xml import *

warnings.warn("DEPRECATED: imported pimlico.old_datatypes. Switch to using new datatypes in pimlico.datatypes",
              stacklevel=2)


__all__ = \
    coref.__all__ + parse.__all__ + arrays.__all__ + base.__all__ + caevo.__all__ + dictionary.__all__ + \
    features.__all__ + jsondoc.__all__ + tar.__all__ + tokenized.__all__ + word_annotations.__all__ + xml.__all__ + \
    documents.__all__
