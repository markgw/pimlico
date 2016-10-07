import os
import sys
from pimlico.core.dependencies.base import check_and_install
from pimlico.core.dependencies.core import CORE_PIMLICO_DEPENDENCIES

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


def install_core_dependencies():
    # Always check that core dependencies are satisfied before running anything
    unavailable = [dep for dep in CORE_PIMLICO_DEPENDENCIES if not dep.available()]
    if len(unavailable):
        print >>sys.stderr, "Some core Pimlico dependencies are not available: %s\n" % \
                            ", ".join(dep.name for dep in unavailable)
        uninstalled = check_and_install(CORE_PIMLICO_DEPENDENCIES)
        if len(uninstalled):
            print >>sys.stderr, "Unable to install all core dependencies: exiting"
            sys.exit(1)
