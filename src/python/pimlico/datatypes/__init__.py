# Import datatypes here to make it easier to specify their paths in config files
from . import coref
from .coref import *
from . import parse
from .parse import *
from . import arrays
from .arrays import *
from . import base
from .base import *
from . import caevo
from .caevo import *
from . import dictionary
from .dictionary import *
from . import features
from .features import *
from . import jsondoc
from .jsondoc import *
from . import tar
from .tar import *
from . import tokenized
from .tokenized import *
from . import word_annotations
from .word_annotations import *
from . import xml
from .xml import *

__all__ = \
    coref.__all__ + parse.__all__ + arrays.__all__ + base.__all__ + caevo.__all__ + dictionary.__all__ + \
    features.__all__ + jsondoc.__all__ + tar.__all__ + tokenized.__all__ + word_annotations.__all__ + xml.__all__
