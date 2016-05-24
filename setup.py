"""
Basic setup of Pimlico.
This is provided primarily so that the docs can be built on the ReadTheDocs server and can import all the
code, including basic dependencies.

"""
import sys
import os


sys.path.insert(0, os.path.abspath('src/python'))

# Install the basic, core Pimlico dependencies
from pimlico import install_core_dependencies
install_core_dependencies()
