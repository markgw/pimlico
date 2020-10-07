# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os
from pimlico import MODEL_DIR


def abs_path_or_model_dir_path(path, model_type):
    if not os.path.isabs(path):
        # Assumed to be in model dir
        return os.path.join(MODEL_DIR, model_type, path)
    else:
        return path
