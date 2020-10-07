# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Tools for Python library dependencies.

Provides superclasses for Python library dependencies and a selection of commonly used dependency instances.

"""
from builtins import str
import sys
from past.builtins import reload
from pkgutil import find_loader

from pimlico.core.dependencies.licenses import GNU_LGPL_V2, BSD, APACHE_V2, MIT

import pkg_resources
from pkg_resources import parse_version, parse_requirements

from pimlico.core.dependencies.base import SoftwareDependency


class PythonPackageDependency(SoftwareDependency):
    """
    Base class for Python dependencies. Provides import checks, but no installation routines. Subclasses should
    either provide install() or installation_instructions().

    The import checks do not (as of 0.6rc) actually import the package, as this may have side-effects that are
    difficult to account for, causing odd things to happen when you check multiple times, or try to import later.
    Instead, it just checks whether the package finder is about to locate the package. This doesn't guarantee that
    the import will succeed.

    """
    def __init__(self, package, name, **kwargs):
        super(PythonPackageDependency, self).__init__(name, **kwargs)
        self.package = package

    def problems(self, local_config):
        probs = super(PythonPackageDependency, self).problems(local_config)
        # To avoid having any impact on the system state during this check, we don't try actually importing the package
        try:
            pkg_loader = find_loader(self.package)
        except ImportError:
            probs.append("could not find loader to try locating %s" % self.package)
        else:
            if pkg_loader is None:
                probs.append("package importer could not locate %s" % self.package)
        return probs

    def import_package(self):
        """
        Try importing package_name. By default, just uses `__import__`. Allows subclasses to allow for
        special import behaviour.

        Should raise an `ImportError` if import fails.

        """
        return __import__(self.package)

    def get_installed_version(self, local_config):
        """
        Tries to import a __version__ variable from the package, which is a standard way to define the package version.

        """
        # Import the package
        # We're allowed to assume that available() returns True, so this import should work
        pck = self.import_package()
        # Try a load of different names that would denote the version string
        possible_names = ["__version__", "__VERSION__", "__release__"]
        for var_name in possible_names:
            if hasattr(pck, var_name):
                return str(getattr(pck, var_name))
        # None of these worked: fall back to default behaviour
        return super(PythonPackageDependency, self).get_installed_version(local_config)

    def __eq__(self, other):
        return isinstance(other, PythonPackageDependency) and self.package == other.package

    def __hash__(self):
        return hash(self.package)


class PythonPackageSystemwideInstall(PythonPackageDependency):
    """
    Dependency on a Python package that needs to be installed system-wide.

    """
    def __init__(self, package_name, name, pip_package=None, apt_package=None, yum_package=None, **kwargs):
        super(PythonPackageSystemwideInstall, self).__init__(package_name, name, **kwargs)
        self.pip_package = pip_package
        self.apt_package = apt_package
        self.yum_package = yum_package

    def installable(self):
        return False

    def installation_instructions(self):
        if self.pip_package is not None:
            pip_message = "\n\nInstall with Pip using:\n    pip install '%s'" % self.pip_package
        else:
            pip_message = ""
        if self.apt_package is not None:
            apt_message = "\n\nOn Ubuntu/Debian systems, install using:\n    sudo apt-get install %s" % self.apt_package
        else:
            apt_message = ""
        if self.yum_package is not None:
            yum_message = "\n\nOn Red Hat/Fedora systems, install using:\n    sudo yum install %s" % self.yum_package
        else:
            yum_message = ""
        return "This Python library must be installed system-wide (which requires superuser privileges)%s%s%s" % \
               (pip_message, apt_message, yum_message)


class PythonPackageOnPip(PythonPackageDependency):
    """
    Python package that can be installed via pip. Will be installed in the virtualenv if not available.

    Allows specification of a minimum version. If an earlier version is installed,
    it will be upgraded.

    Name is the readable software name. Package is a the package that is imported in Python.

    """
    def __init__(self, package, name=None, pip_package=None, upgrade_only_if_needed=False, min_version=None, editable=False, **kwargs):
        """
        :type editable: boolean
        :param editable: Pass the --editable option to pip when installing. Use with e.g. Git urls as packages.
        """
        self.editable = editable
        self.min_version = min_version
        self.upgrade_only_if_needed = upgrade_only_if_needed
        # Package names tend to be identical to the software name, so there's no need to specify both
        if name is None:
            name = package
        # If pip_package is given, use that as pip install target instead of package name
        # For cases where Python package name doesn't coincide with install target
        self.pip_package = pip_package or package
        super(PythonPackageOnPip, self).__init__(package, name, **kwargs)

    def installable(self):
        return True

    def install(self, local_config, trust_downloaded_archives=False):
        import subprocess
        options = []
        if self.upgrade_only_if_needed:
            options.extend(["--upgrade-strategy", "only-if-needed"])
        elif self.min_version is not None:
            options.append("--upgrade")

        if self.editable:
            options.append("--editable")

        if self.min_version is not None:
            package = "{}>={}".format(self.pip_package, self.min_version)
        else:
            package = self.pip_package

        # Use subprocess to call Pip: the recommended way to use it programmatically
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-warn-script-location'] + options + [package])

        # Refresh sys.path so we can import the installed package
        import site
        reload(site)

    def problems(self, local_config):
        problems = super(PythonPackageOnPip, self).problems(local_config)
        if not problems and self.min_version is not None:
            # Also check that it's a sufficient version
            inst_version = self.get_installed_version(local_config)
            if parse_version(self.min_version) > parse_version(inst_version):
                problems.append("{} is installed, but only version {}: {} required".format(
                    self.name, inst_version, self.min_version
                ))
        return problems

    def __repr__(self):
        return "PythonPackageOnPip<%s%s>" % (self.name, (" (%s)" % self.package) if self.package != self.name else "")

    def get_installed_version(self, local_config):
        reqs = list(parse_requirements(self.package))
        if len(reqs) != 1:
            raise ValueError("pip_package='{}', which could not be parsed as a requirement".format(self.package))
        # Reload the working set in case something's been installed since loaded
        reload(pkg_resources)
        # Look up the package
        dist = pkg_resources.working_set.find(reqs[0])
        if dist is None:
            # Pip package not found
            # This can happen because the package wasn't installed with Pip, but is available because it's importable
            return super(PythonPackageOnPip, self).get_installed_version(local_config)
        else:
            # Found the Pip package info: this contains the version
            return dist.version


###################################
# Some commonly used dependencies #
###################################

urwid_dependency = PythonPackageOnPip("urwid", homepage_url="http://urwid.org/", license=GNU_LGPL_V2)
numpy_dependency = PythonPackageOnPip("numpy", "Numpy", homepage_url="https://numpy.org/", license=BSD)
scipy_dependency = PythonPackageOnPip("scipy", "Scipy", homepage_url="https://www.scipy.org/", license=BSD)
theano_dependency = PythonPackageOnPip("theano", pip_package="Theano")
tensorflow_dependency = PythonPackageOnPip("tensorflow", homepage_url="https://www.tensorflow.org/", license=APACHE_V2)
# We usually need h5py for reading/storing models
h5py_dependency = PythonPackageOnPip("h5py", pip_package="h5py", homepage_url="https://www.h5py.org/", license=BSD)
# This version of the Keras dependency assumes we're using the theano backend
keras_theano_dependency = PythonPackageOnPip("keras", dependencies=[theano_dependency, h5py_dependency],
                                             homepage_url="https://keras.io/", license=MIT)
keras_tensorflow_dependency = PythonPackageOnPip("keras", dependencies=[tensorflow_dependency, h5py_dependency],
                                                 homepage_url="https://keras.io/", license=MIT)
# This version does not depend on any of the backend packages
# This allows you to be ambivalent about which one is used, but means the package is not checked
keras_dependency = PythonPackageOnPip("keras", dependencies=[h5py_dependency],
                                      homepage_url="https://keras.io/", license=MIT)
pytorch_dependency = PythonPackageOnPip("torch", "PyTorch", homepage_url="https://pytorch.org/")
pyro_dependency = PythonPackageOnPip("pyro", "Pyro", pip_package="pyro-ppl", dependencies=[pytorch_dependency],
                                     homepage_url="http://pyro.ai/", license=APACHE_V2)

sklearn_dependency = PythonPackageOnPip(
    "sklearn", "Scikit-learn", pip_package="scikit-learn", dependencies=[numpy_dependency, scipy_dependency],
    homepage_url="https://scikit-learn.org/stable/", license=BSD
)
pandas_dependency = PythonPackageOnPip("pandas", homepage_url="https://pandas.pydata.org/", license=BSD)

# Gensim relies on Requests, which needs urllib3>=1.23 to work,
# but this isn't enforced in the dependencies
requests_dependency = PythonPackageOnPip("requests", min_version="2.20")
gensim_dependency = PythonPackageOnPip(
    "gensim", "Gensim",
    dependencies=[numpy_dependency, scipy_dependency, requests_dependency],
    upgrade_only_if_needed=True,
    # In 3.3.0 embedding storage was changed, so it's important we're on the right
    # side of that release
    min_version="3.3.0",
    homepage_url="https://radimrehurek.com/gensim/", license=GNU_LGPL_V2,
)

spacy_dependency = PythonPackageOnPip("spacy", homepage_url="https://spacy.io/", license=MIT)
fasttext_dependency = PythonPackageOnPip("fasttext", homepage_url="https://fasttext.cc/", license=MIT)


### Special behaviour for bs4

def safe_import_bs4():
    """
    BS can go very slowly if it tries to use chardet to detect input encoding
    Remove chardet and cchardet from the Python modules, so that import fails and it doesn't try to use them
    This prevents it getting stuck on reading long input files

    """
    import sys
    sys.modules["cchardet"] = None
    sys.modules["chardet"] = None
    # Now we can import BS
    import bs4
    return bs4


class BeautifulSoupDependency(PythonPackageOnPip):
    """
    Test import with special BS import behaviour.

    """
    def __init__(self):
        super(BeautifulSoupDependency, self).__init__(
            "bs4", pip_package="beautifulsoup4", name="Beautiful Soup",
            homepage_url="https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            license=MIT,
        )

    def import_package(self):
        return safe_import_bs4()

beautiful_soup_dependency = BeautifulSoupDependency()



nltk_dependency = PythonPackageOnPip("nltk", "NLTK", homepage_url="https://www.nltk.org/", license=APACHE_V2)


class NLTKResource(SoftwareDependency):
    """
    Check for and install NLTK resources, using NLTK's own downloader.

    """
    def problems(self, local_config):
        problems = super(NLTKResource, self).problems(local_config)
        # Check whether the resource is available
        try:
            from nltk.downloader import _downloader
        except:
            # If NLTK isn't even installed, we can't check whether the resource is there
            problems.append("NLTK not installed: cannot check for resource '{}'".format(self.name))
        else:
            try:
                resource_installed = _downloader.is_installed(self.name)
            except Exception as e:
                problems.append("Error checking NLTK resource status for {}: {}".format(self.name, e))
            else:
                if not resource_installed:
                    problems.append("NLTK resource '{}' not installed".format(self.name))
        return problems

    def installable(self):
        return True

    def install(self, local_config, trust_downloaded_archives=False):
        from nltk import download
        download(self.name)

    def dependencies(self):
        return super(NLTKResource, self).dependencies() + [nltk_dependency]
