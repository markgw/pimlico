
"""
Core dependencies required by the basic Pimlico installation, regardless of what pipeline is being processed.

"""
from pimlico.core.dependencies.python import PythonPackageSystemwideInstall, PythonPackageOnPip

CORE_PIMLICO_DEPENDENCIES = [
    # Virtualenv must be installed so that we can install other packages in the local Pimlico environment
    PythonPackageSystemwideInstall("virtualenv", "Virtualenv"),
    # Several lightweight Python libraries that we use throughout the codebase
    PythonPackageOnPip("progressbar", "Progressbar"),
    PythonPackageOnPip("tabulate", "tabulate"),
    PythonPackageOnPip("termcolor", "termcolor"),
]
