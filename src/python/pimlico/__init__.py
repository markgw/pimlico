import os

__version__ = "0.1"
PIMLICO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
LIB_DIR = os.path.join(PIMLICO_ROOT, "lib")
JAVA_LIB_DIR = os.path.join(LIB_DIR, "java")
JAVA_BUILD_DIR = os.path.join(PIMLICO_ROOT, "build")
MODEL_DIR = os.path.join(PIMLICO_ROOT, "models")
