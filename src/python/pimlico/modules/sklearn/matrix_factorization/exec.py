from pimlico.core.config import PipelineConfigParseError
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.arrays import NumpyArrayWriter
from pimlico.modules.sklearn.matrix_factorization.info import SKLEARN_CLASSES


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_matrix = self.info.get_input("matrix").array
        self.log.info("Loaded input matrix: %s" % str(input_matrix.shape))

        transform_type = self.info.options["class"]
        # Check known properties of this type of transformation
        transform_props = SKLEARN_CLASSES[transform_type]
        # Check whether this type is able to accept sparse input
        if transform_props["sparse"]:
            # Convert to CSR, which is better for most purposes
            input_matrix = input_matrix.tocsr()
        else:
            # We need to transform the matrix to a dense array
            # This could cause problems with large matrices, in which case you need to use a different transform type
            self.log.info("%s transformation requires dense input: converting matrix" % transform_type)
            input_matrix = input_matrix.toarray()

        # Try initializing the transformation
        self.log.info(
            "Initializing %s with options: %s" %
            (transform_type, ", ".join("%s=%s" % (key, val) for (key, val) in self.info.init_kwargs.items()))
        )
        transform_cls = self.info.load_transformer_class()
        try:
            transformer = transform_cls(**self.info.init_kwargs)
        except TypeError, e:
            raise PipelineConfigParseError("invalid arguments to %s: %s" % (transform_type, e))

        # Apply transformation to the matrix
        self.log.info("Fitting %s transformation on input matrix" % transform_type)
        transformed_matrix = transformer.fit_transform(input_matrix)
        self.log.info("Fitting complete: storing H and W matrices")

        with NumpyArrayWriter(self.info.get_absolute_output_dir("w")) as w_writer:
            w_writer.set_array(transformed_matrix)
        with NumpyArrayWriter(self.info.get_absolute_output_dir("h")) as h_writer:
            h_writer.set_array(transformer.components_)
