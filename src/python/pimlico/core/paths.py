import os
from pimlico import MODEL_DIR


def abs_path_or_model_dir_path(path, model_type):
    if not os.path.isabs(path):
        # Assumed to be in model dir
        return os.path.join(MODEL_DIR, model_type, path)
    else:
        return path
