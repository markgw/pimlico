import os

from pimlico.core.dependencies.python import PythonPackageOnPip
from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter

__all__ = ["Word2VecModel", "Word2VecModelWriter"]


class Word2VecModel(PimlicoDatatype):
    def __init__(self, base_dir, pipeline, **kwargs):
        super(Word2VecModel, self).__init__(base_dir, pipeline, **kwargs)

    def data_ready(self):
        return super(Word2VecModel, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "vectors.bin"))

    def load_model(self):
        from gensim.models.word2vec import Word2Vec
        return Word2Vec.load_word2vec_format(os.path.join(self.data_dir, "vectors.bin"), binary=True)

    def get_software_dependencies(self):
        # Depend on Gensim, which can be installed using Pip
        return super(Word2VecModel, self).get_software_dependencies() + [
            PythonPackageOnPip("gensim")
        ]


class Word2VecModelWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(Word2VecModelWriter, self).__init__(base_dir)
        self.word2vec_model = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Word2VecModelWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if self.word2vec_model is not None:
            self.word2vec_model.save_word2vec_format(os.path.join(self.data_dir, "vectors.bin"), binary=True)
