# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
""" Basic Pimlico core dependencies """

from future.utils import PY2
from pimlico.core.dependencies.licenses import MIT, BSD, PSF, BSD_2CLAUSE

from pimlico.core.dependencies.python import PythonPackageOnPip

#: Core dependencies required by the basic Pimlico installation, regardless of what pipeline is being processed.
#: These will be checked when Pimlico is run, using the same dependency-checking mechanism that Pimlico modules
#: use, and installed automatically if they're not found.
CORE_PIMLICO_DEPENDENCIES = [
    # We use the future library to provide Python 2-3 compatibility, but this has to be installed before we get this far
    # Since we're always running in a virtualenv, we can assume that Pip is availble.
    # We've actually already checked its version and potentially upgraded by this point.
    # Virtualenv must be installed so that we can install other packages in the local Pimlico environment
    # Note that, even within a running virtualenv, the virtualenv Python package might not be installed
    # In this case, it can be installed using Pip
    PythonPackageOnPip("virtualenv", homepage_url="https://virtualenv.pypa.io/en/latest/", license=MIT),
    # Several lightweight Python libraries that we use throughout the codebase
    PythonPackageOnPip("colorama", "colorama", homepage_url="https://github.com/tartley/colorama", license=BSD),
    PythonPackageOnPip("termcolor", "termcolor", homepage_url="https://pypi.org/project/termcolor/", license=BSD),
    PythonPackageOnPip("tabulate", "tabulate", homepage_url="https://github.com/astanin/python-tabulate", license=MIT),
    PythonPackageOnPip("progressbar", "Progressbar", homepage_url="https://pypi.org/project/progressbar/", license=BSD),
    # Backport of CSV reading, so we can handle unicode in the same way on Py 2 and 3
    PythonPackageOnPip("backports.csv", homepage_url="https://pypi.org/project/backports.csv/", license=PSF),
    PythonPackageOnPip("tblib", homepage_url="https://pypi.org/project/tblib/", license=BSD_2CLAUSE),
]

# Python 2-only dependencies
if PY2:
    CORE_PIMLICO_DEPENDENCIES.extend([
        # Provides a backport of Py3's updated and renamed configparser package
        PythonPackageOnPip("configparser"),
    ])


coloredlogs_dependency = PythonPackageOnPip("coloredlogs")
