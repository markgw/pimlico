"""
The Pimlico Processing Toolkit (PIpelined Modular LInguistic COrpus processing) is a toolkit for building pipelines
made up of linguistic processing tasks to run on large datasets (corpora). It provides a wrappers around many
existing, widely used NLP (Natural Language Processing) tools.

"""
from __future__ import print_function
import os
import sys
import subprocess

# Core dependencies will be checked when Pimlico is run and installed if necessary.
# However, future is needed right away, before we can even start importing
# the code to install the core deps, since that code needs to be Py2-3 compatible
try:
    import future
except ImportError:
    print("Future library is not installed: installing now")
    # Call pip to install future
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'future'])
    # Reload the environment, so we see the newly install package(s)
    import site
    try:
        # importlib is preferred over imp
        from importlib import reload
    except ImportError:
        try:
            # In early Python3 versions, use imp
            from imp import reload
        except ImportError:
            # In Python2 it's a builtin, so try just skipping
            pass
    reload(site)

from pimlico.core.dependencies.base import check_and_install
from pimlico.core.dependencies.core import CORE_PIMLICO_DEPENDENCIES, coloredlogs_dependency

PIMLICO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

# Fetch current version number from PIMLICO_ROOT/admin/release.txt
with open(os.path.join(PIMLICO_ROOT, "admin", "release.txt"), "r") as releases_file:
    _lines = [r.strip() for r in releases_file.read().splitlines()]
    releases = [r[1:] for r in _lines if r.startswith("v")]
# The last listed version is the current, bleeding-edge version number
# This file used to contain all release numbers, but we now get them from git tags
# The only information given in the file now is the current version
__version__ = releases[-1]

PROJECT_ROOT = os.path.abspath(os.path.join(PIMLICO_ROOT, ".."))

LIB_DIR = os.path.join(PIMLICO_ROOT, "lib")
JAVA_LIB_DIR = os.path.join(LIB_DIR, "java")
JAVA_BUILD_JAR_DIR = os.path.join(PIMLICO_ROOT, "build", "jar")
MODEL_DIR = os.path.join(PIMLICO_ROOT, "models")
LOG_DIR = os.path.join(PIMLICO_ROOT, "log")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
EXAMPLES_DIR = os.path.join(PIMLICO_ROOT, "examples")
TEST_DATA_DIR = os.path.join(PIMLICO_ROOT, "test", "data")
TEST_STORAGE_DIR = os.path.join(PIMLICO_ROOT, "test", "storage")
# Root URL for generating links to Pimlico source code in the docs
REPO_SOURCE_HTML_ROOT = "https://github.com/markgw/pimlico/blob/master/"


def install_core_dependencies():
    # Always check that core dependencies are satisfied before running anything
    # Core dependencies are not allowed to depend on the local config, as we can't get to it at this point
    # We just pass in an empty dictionary
    unavailable = [dep for dep in CORE_PIMLICO_DEPENDENCIES if not dep.available({})]
    if len(unavailable):
        print("Some core Pimlico dependencies are not available: %s\n" % \
                            ", ".join(dep.name for dep in unavailable), file=sys.stderr)
        uninstalled = check_and_install(CORE_PIMLICO_DEPENDENCIES, {})
        if len(uninstalled):
            print("Unable to install all core dependencies: exiting", file=sys.stderr)
            sys.exit(1)

    # Special procedure for coloredlogs
    # This is nice to have, but if we can't install it or load it, it's not a problem
    try:
        if not coloredlogs_dependency.available({}):
            print("Installing coloredlogs")
            coloredlogs_dependency.install({})
        # Load coloredlogs and start using it for all logging formatters
        import coloredlogs
        coloredlogs.install()
    except Exception as e:
        print("Error installing and loading colorlogs. Logs will not be coloured. {}".format(e))


def get_jupyter_pipeline():
    """
    Special function to get access to a currently loaded pipeline from a Jupyter notebook.

    """
    from pimlico.utils.jupyter import get_pipeline
    return get_pipeline()
