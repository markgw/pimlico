# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Wrappers around Numpy arrays and Scipy sparse matrices.

"""

from builtins import object

from pimlico.core.dependencies.python import numpy_dependency, scipy_dependency
from pimlico.datatypes.files import NamedFileCollection
from pimlico.utils.core import cached_property
from io import open

__all__ = ["NumpyArray", "ScipySparseMatrix"]


class NumpyArray(NamedFileCollection):
    """
    .. todo:

       Add unit test for numpy array

    """
    datatype_name = "numpy_array"
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(NumpyArray, self).__init__(["array.npy"], *args, **kwargs)

    def get_software_dependencies(self):
        return super(NumpyArray, self).get_software_dependencies() + [numpy_dependency]

    class Reader(object):
        @cached_property
        def array(self):
            import numpy
            with open(self.get_absolute_path("array.npy"), "rb") as f:
                return numpy.load(f)

    class Writer(object):
        def write_array(self, array):
            import numpy
            numpy.save(self.get_absolute_path("array.npy"), array)
            self.file_written("array.npy")


class ScipySparseMatrix(NamedFileCollection):
    """
    Wrapper around Scipy sparse matrices. The matrix loaded is always in COO format -- you probably want to convert
    to something else before using it. See scipy docs on sparse matrix conversions.

    .. todo:

       Add unit test for scipy matrix

    """
    datatype_name = "scipy_sparse_array"
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(ScipySparseMatrix, self).__init__(["array.mtx"], *args, **kwargs)

    def get_software_dependencies(self):
        return super(ScipySparseMatrix, self).get_software_dependencies() + [scipy_dependency, numpy_dependency]

    class Reader(object):
        @cached_property
        def array(self):
            from scipy import io
            return io.mmread(self.get_absolute_path("array.mtx"))

    class Writer(object):
        def write_matrix(self, mat):
            from scipy.sparse import coo_matrix
            from scipy.io import mmwrite

            if type(mat) is not coo_matrix:
                # If this isn't a COO matrix, try converting it
                # Other scipy sparse matrix types and numpy dense arrays can all be converted in this way
                mat = coo_matrix(mat)

            mmwrite(self.get_absolute_path("array.mtx"), mat)
            self.file_written("array.mtx")
