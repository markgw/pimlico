"""
Called if a virtual environment has not yet been set up for this Pimlico environment.

"""
from __future__ import print_function
import os

import sys

try:
    import virtualenv
except ImportError:
    print("ERROR: Virtualenv must be installed to start using a Pimlico project.")
    print("  Configuration script could not import virtualenv Python package.")
    print("  Current Python interpreter: {}".format(sys.executable))
    print("  See https://virtualenv.pypa.io/en/latest/ for details of Virtualenv installation")
    sys.exit(1)
from virtualenv import create_environment


lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if len(sys.argv) > 1:
    # Allow alternative env location to be specified
    virtualenv_dir = sys.argv[1]
else:
    virtualenv_dir = os.path.join(lib_dir, "python_env")

if not os.path.exists(virtualenv_dir):
    os.makedirs(virtualenv_dir)

# Make a new virtualenv that will be used by Pimlico to install software
print("Creating new virtualenv in %s for installing Python software" % virtualenv_dir)
create_environment(virtualenv_dir, site_packages=True)
