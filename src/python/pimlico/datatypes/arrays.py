# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Wrappers around Numpy arrays and Scipy sparse matrices.

"""
import os

from pimlico.core.dependencies.python import numpy_dependency, scipy_dependency
from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter
from pimlico.datatypes.files import FileCollection

__all__ = ["NumpyArray", "NumpyArrayWriter", "ScipySparseMatrix", "ScipySparseMatrixWriter"]


class NumpyArray(FileCollection):
    datatype_name = "numpy_array"
    filenames = ["array.npy"]

    def __init__(self, base_dir, pipeline, **kwargs):
        super(NumpyArray, self).__init__(base_dir, pipeline, **kwargs)
        self._array = None

    @property
    def array(self):
        if self._array is None:
            import numpy
            with open(os.path.join(self.data_dir, "array.npy"), "r") as f:
                self._array = numpy.load(f)
        return self._array

    def get_software_dependencies(self):
        return super(NumpyArray, self).get_software_dependencies() + [numpy_dependency]


class NumpyArrayWriter(PimlicoDatatypeWriter):
    def set_array(self, array):
        import numpy
        numpy.save(os.path.join(self.data_dir, "array.npy"), array)


class ScipySparseMatrix(PimlicoDatatype):
    """
    Wrapper around Scipy sparse matrices. The matrix loaded is always in COO format -- you probably want to convert
    to something else before using it. See scipy docs on sparse matrix conversions.

    """
    datatype_name = "scipy_sparse_array"
    filenames = ["array.mtx"]

    def __init__(self, base_dir, pipeline, **kwargs):
        super(ScipySparseMatrix, self).__init__(base_dir, pipeline, **kwargs)
        self._array = None

    @property
    def array(self):
        if self._array is None:
            from scipy import io
            self._array = io.mmread(os.path.join(self.data_dir, "array.mtx"))
        return self._array

    def get_software_dependencies(self):
        return super(ScipySparseMatrix, self).get_software_dependencies() + [scipy_dependency, numpy_dependency]


class ScipySparseMatrixWriter(PimlicoDatatypeWriter):
    def set_matrix(self, mat):
        from scipy.sparse import coo_matrix
        from scipy.io import mmwrite

        if type(mat) is not coo_matrix:
            # If this isn't a COO matrix, try converting it
            # Other scipy sparse matrix types and numpy dense arrays can all be converted in this way
            mat = coo_matrix(mat)

        mmwrite(os.path.join(self.data_dir, "array.mtx"), mat)
