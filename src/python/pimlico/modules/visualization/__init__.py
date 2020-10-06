"""
Visualization tools

Modules for plotting and suchlike

"""
from pimlico.core.dependencies.licenses import SoftwareLicense

from pimlico.core.dependencies.python import PythonPackageOnPip

MATPLOTLIB_LICENSE = SoftwareLicense(
    "Matplotlib BSD-compatible",
    url="https://matplotlib.org/3.1.0/devel/license.html",
    description="Custom license, BSD compatible"
)

matplotlib_dependency = PythonPackageOnPip(
    "matplotlib", name="Matplotlib", homepage_url="https://matplotlib.org/", license=MATPLOTLIB_LICENSE
)
