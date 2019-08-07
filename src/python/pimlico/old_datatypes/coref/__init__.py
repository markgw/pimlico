from __future__ import absolute_import
from .corenlp import CorefCorpus as CoreNLPCorefCorpus, CorefCorpusWriter as CoreNLPCorefCorpusWriter
from .opennlp import CorefCorpus as OpenNLPCorefCorpus, CorefCorpusWriter as OpenNLPCorefCorpusWriter

__all__ = [
    "OpenNLPCorefCorpus", "OpenNLPCorefCorpusWriter",
    "CoreNLPCorefCorpus", "CoreNLPCorefCorpusWriter",
]
