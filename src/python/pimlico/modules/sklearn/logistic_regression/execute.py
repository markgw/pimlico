# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.utils import shuffle

from pimlico.core.config import PipelineConfigParseError
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        features = self.info.get_input("features")
        # Set the dimensionality based on total features, even if they're not all used
        num_features = len(features.feature_types)

        data = []
        rows = []
        cols = []
        scores = []
        # Don't translate the stored feature IDs back to names, but keep them as raw IDs
        row_num = -1
        for row_num, (features, score) in enumerate(features.iter_ids()):
            scores.append(score)

            for feat_id, val in features.iteritems():
                data.append(val)
                rows.append(row_num)
                cols.append(feat_id)

        # Read the features into a sparse matrix
        input_data = csr_matrix((data, (rows, cols)), shape=(row_num+1, num_features))
        scores = np.array(scores)
        self.log.info("Loaded input matrix: %s" % str(input_data.shape))

        # Try initializing the transformation
        lr_init_kwargs = self.info.options["options"]
        self.log.info(
            "Initializing LogisticRegression with options: {}".format(
                ", ".join("%s=%s" % (key, val) for (key, val) in lr_init_kwargs))
        )
        try:
            log_reg = LogisticRegression(**lr_init_kwargs)
        except TypeError, e:
            raise PipelineConfigParseError("invalid arguments to LogisticRegression: {}".format(e))

        # Shuffle the rows of the training data, so that the source providing the
        # data doesn't need to do this
        input_data = shuffle(input_data)

        # Apply transformation to the matrix
        self.log.info("Fitting logistic regression on input matrix")
        log_reg.fit(input_data, scores)
        self.log.info("Fitting complete: storing model")

        with self.info.get_output_writer() as writer:
            writer.save_model(log_reg)
