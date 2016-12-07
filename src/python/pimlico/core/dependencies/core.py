""" Basic Pimlico core dependencies """
from pimlico.core.dependencies.python import PythonPackageSystemwideInstall, PythonPackageOnPip

#: Core dependencies required by the basic Pimlico installation, regardless of what pipeline is being processed.
#: These will be checked when Pimlico is run, using the same dependency-checking mechanism that Pimlico modules
#: use, and installed automatically if they're not found.
CORE_PIMLICO_DEPENDENCIES = [
    # Virtualenv must be installed so that we can install other packages in the local Pimlico environment
    PythonPackageSystemwideInstall("virtualenv", "Virtualenv"),
    # Several lightweight Python libraries that we use throughout the codebase
    PythonPackageOnPip("progressbar", "Progressbar"),
    PythonPackageOnPip("tabulate", "tabulate"),
    PythonPackageOnPip("colorama", "colorama"),
    PythonPackageOnPip("termcolor", "termcolor"),
]
