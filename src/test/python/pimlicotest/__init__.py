import os
from pimlico import EXAMPLES_DIR


def example_path(*path_within_examples):
    return os.path.join(EXAMPLES_DIR, *path_within_examples)
