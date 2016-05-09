"""
Wrappers around Numpy arrays and Scipy sparse matrices.

"""
import os

from pimlico.datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter


__all__ = ["NumpyArray", "NumpyArrayWriter", "ScipySparseMatrix", "ScipySparseMatrixWriter"]


class NumpyArray(PimlicoDatatype):
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

    def data_ready(self):
        return super(NumpyArray, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "array.npy"))

    def check_runtime_dependencies(self):
        missing_dependencies = []
        try:
            import numpy
        except ImportError:
            missing_dependencies.append(("Numpy", "install Numpy systemwide (e.g. package 'python-numpy' on Ubuntu)"))
        missing_dependencies.extend(super(NumpyArray, self).check_runtime_dependencies())
        return missing_dependencies


class NumpyArrayWriter(PimlicoDatatypeWriter):
    def set_array(self, array):
        import numpy
        numpy.save(os.path.join(self.data_dir, "array.npy"), array)


class ScipySparseMatrix(PimlicoDatatype):
    """
    Wrapper around Scipy sparse matrices. The matrix loaded is always in COO format -- you probably want to convert
    to something else before using it. See scipy docs on sparse matrix conversions.

    """
    def __init__(self, base_dir, pipeline, **kwargs):
        super(ScipySparseMatrix, self).__init__(base_dir, pipeline, **kwargs)
        self._array = None

    @property
    def array(self):
        if self._array is None:
            from scipy import io
            self._array = io.mmread(os.path.join(self.data_dir, "array.mtx"))
        return self._array

    def data_ready(self):
        return super(ScipySparseMatrix, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "array.mtx"))

    def check_runtime_dependencies(self):
        missing_dependencies = []
        try:
            import numpy
        except ImportError:
            missing_dependencies.append(("Numpy", "install Numpy systemwide (e.g. package 'python-numpy' on Ubuntu)"))
        try:
            import scipy
        except ImportError:
            missing_dependencies.append(("Scipy", "install Scipy systemwide (e.g. package 'python-scipy' on Ubuntu)"))
        missing_dependencies.extend(super(ScipySparseMatrix, self).check_runtime_dependencies())
        return missing_dependencies


class ScipySparseMatrixWriter(PimlicoDatatypeWriter):
    def set_matrix(self, mat):
        from scipy.sparse import coo_matrix
        from scipy.io import mmwrite

        if type(mat) is not coo_matrix:
            # If this isn't a COO matrix, try converting it
            # Other scipy sparse matrix types and numpy dense arrays can all be converted in this way
            mat = coo_matrix(mat)

        mmwrite(os.path.join(self.data_dir, "array.mtx"), mat)
