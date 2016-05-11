# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os
from pimlico import MODEL_DIR


def abs_path_or_model_dir_path(path, model_type):
    if not os.path.isabs(path):
        # Assumed to be in model dir
        return os.path.join(MODEL_DIR, model_type, path)
    else:
        return path
