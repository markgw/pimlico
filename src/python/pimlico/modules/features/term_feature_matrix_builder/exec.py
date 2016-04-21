import numpy
from scipy.sparse.dok import dok_matrix

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.arrays import ScipySparseMatrixWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_data = self.info.get_input("data")

        self.log.info("Collecting features into a %d x %d sparse matrix from %d data points" %
                      (len(input_data.term_dictionary), len(input_data.feature_dictionary), len(input_data)))
        pbar = get_progress_bar(len(input_data), title="Collecting")

        matrix = dok_matrix((len(input_data.term_dictionary), len(input_data.feature_dictionary)), dtype=numpy.int32)
        # Iterate over the input data and collect up counts from all instances of each term
        for term, feature_counts in pbar(input_data):
            for feature, count in feature_counts.items():
                matrix[term, feature] += count

        # Write out the matrix
        self.log.info("Built matrix: writing to disk")
        with ScipySparseMatrixWriter(self.info.get_absolute_output_dir("matrix")) as writer:
            # Matrix will be converted to COO format before writing
            writer.set_matrix(matrix)
