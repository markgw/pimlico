# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

""" Basic Pimlico core dependencies """
from pimlico.core.dependencies.python import PythonPackageSystemwideInstall, PythonPackageOnPip

#: Core dependencies required by the basic Pimlico installation, regardless of what pipeline is being processed.
#: These will be checked when Pimlico is run, using the same dependency-checking mechanism that Pimlico modules
#: use, and installed automatically if they're not found.
CORE_PIMLICO_DEPENDENCIES = [
    # Virtualenv must be installed so that we can install other packages in the local Pimlico environment
    PythonPackageSystemwideInstall("virtualenv", "Virtualenv"),
    # Several lightweight Python libraries that we use throughout the codebase
    PythonPackageOnPip("colorama", "colorama"),
    PythonPackageOnPip("termcolor", "termcolor"),
    PythonPackageOnPip("tabulate", "tabulate"),
    PythonPackageOnPip("progressbar", "Progressbar"),
]
