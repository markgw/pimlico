import os

from pimlico.datatypes.base import PimlicoDatatype


class File(PimlicoDatatype):
    """
    Simple datatype that supplies a single file, providing the path to it.

    This is an abstract class: subclasses need to provide a way of getting to (e.g. storing) the filename in
    question.

    """
    datatype_name = "file"

    def data_ready(self):
        if not super(File, self).data_ready():
            return False
        try:
            # Check that the file that our path points to also exists
            if not os.path.exists(self.absolute_path):
                return False
        except IOError:
            # Subclasses may raise an IOError while trying to compute the path: in this case it's assumed not ready
            return False

    @property
    def absolute_path(self):
        raise NotImplementedError


def NamedFile(name):
    """
    Datatype factory that produces something like a `File` datatype, pointing to a single file, but doesn't store
    its path, just refers to a particular file in the data dir.

    :param name: name of the file
    :return: datatype class
    """
    class _NamedFile(File):
        datatype_name = "named_file"

        @property
        def absolute_path(self):
            return os.path.join(self.data_dir, name)
    return _NamedFile
