from pimlico.datatypes import NamedFileCollection


class GloveOutput(NamedFileCollection):
    """
    Just a small collection of files, providing everything that GloVe outputs
    in the exact form it is produced.

    """
    def __init__(self, *args, **kwargs):
        super(GloveOutput, self).__init__(
            ["cooccurrence.bin", "cooccurrence.shuf.bin", "vectors.txt", "vocab.txt"],
            *args, **kwargs
        )
