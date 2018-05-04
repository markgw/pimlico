# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tools for Python library dependencies.

Provides superclasses for Python library dependencies and a selection of commonly used dependency instances.

"""
import sys
from pkgutil import find_loader

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
        pkg_loader = find_loader(self.package)
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

    """
    def __init__(self, package, name=None, pip_package=None, **kwargs):
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
        
        # Use subprocess to call Pip: the recommended way to use it programmatically
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', self.pip_package])

        # Refresh sys.path so we can import the installed package
        import site
        reload(site)

    def _old_install(self, local_config, trust_downloaded_archives=False):
        """
        This is an old approach to installing programmatically using Pip. Technically, this
        way of using Pip is unsupported and, sure enough, you end up running into horrible
        errors with differing versions of Pip.

        An alternative, more supported approach is now implemented, but this is left
        here in case we need to incorporate anything from it.

        """
        try:
            from pip import __version__
        except ImportError:
            # Very very old versions don't define this
            import pkg_resources
            __version__ = pkg_resources.get_distribution('pip').version

        if int(__version__.split(".")[0]) >= 7:
            # Later version of pip, need to do this differently
            from pip.index import PackageFinder
            from pip.req import InstallRequirement, RequirementSet
            from pip.locations import src_prefix
            from pip.compat import logging_dictConfig
            from pip.utils.logging import IndentingFormatter
            from pip.download import PipSession
            import logging
            from tempfile import mkdtemp
            import shutil

            # Configure logging so we get verbose output
            logging_dictConfig({
                "version": 1,
                "disable_existing_loggers": False,
                "filters": {
                    "exclude_warnings": {
                        "()": "pip.utils.logging.MaxLevelFilter",
                        "level": logging.WARNING,
                    },
                },
                "formatters": {
                    "indent": {
                        "()": IndentingFormatter,
                        "format": "%(message)s",
                    },
                },
                "handlers": {
                    "console": {
                        "level": "DEBUG",
                        "class": "pip.utils.logging.ColorizedStreamHandler",
                        "stream": "ext://sys.stdout",
                        "filters": ["exclude_warnings"],
                        "formatter": "indent",
                    },
                    "console_errors": {
                        "level": "WARNING",
                        "class": "pip.utils.logging.ColorizedStreamHandler",
                        "stream": "ext://sys.stderr",
                        "formatter": "indent",
                    },
                },
                # Previously, got super-verbose debugging by configuring root logger as follows
                # However, this had a horrible effect on later logging
                # Could possibly be solved by removing these handlers after installation. Simplest to stop doing this
                #"root": {
                #    "level": "DEBUG",
                #    "handlers": list(filter(None, [
                #        "console",
                #        "console_errors",
                #        None,
                #    ])),
                #},
                # Disable any logging besides WARNING unless we have DEBUG level
                # logging enabled. These use both pip._vendor and the bare names
                # for the case where someone unbundles our libraries.
                "loggers": dict(
                    (name, {"level": "DEBUG", "handlers": ["console", "console_errors"]})
                    for name in ["pip._vendor", "distlib", "requests", "urllib3"]
                ),
            })

            session = PipSession()

            # Create a temporary build dir
            build_dir = mkdtemp(suffix="pip_build")
            try:
                requirement_set = RequirementSet(build_dir, src_prefix, None, session=session)
                requirement_set.add_requirement(InstallRequirement.from_line(self.pip_package))
            finally:
                shutil.rmtree(build_dir)

            install_options = []
            global_options = []
            finder = PackageFinder(find_links=[], index_urls=["https://pypi.python.org/simple/"], session=session)

            requirement_set.prepare_files(finder)
            # Run installation
            requirement_set.install(install_options, global_options)
        else:
            from pip.index import PackageFinder
            from pip.req import InstallRequirement, RequirementSet
            from pip.locations import build_prefix, src_prefix

            # Enable verbose output
            # NB: This only works on old versions of Pip
            try:
                from pip.log import logger
                logger.add_consumers((logger.INFO, sys.stdout))
            except:
                pass

            # Build a requirement set containing just the package we need
            requirement_set = RequirementSet(build_dir=build_prefix, src_dir=src_prefix, download_dir=None)
            requirement_set.add_requirement(InstallRequirement.from_line(self.pip_package))

            install_options = []
            global_options = []
            finder = PackageFinder(find_links=[], index_urls=["http://pypi.python.org/simple/"])

            requirement_set.prepare_files(finder, force_root_egg_info=False, bundle=False)
            # Run installation
            requirement_set.install(install_options, global_options)
        # Refresh sys.path so we can import the installed package
        import site
        reload(site)

    def __repr__(self):
        return "PythonPackageOnPip<%s%s>" % (self.name, (" (%s)" % self.package) if self.package != self.name else "")

    def get_installed_version(self, local_config):
        from pip.commands.show import search_packages_info
        # Use Pip to get the version number of the installed version
        installed_packages = list(search_packages_info(self.pip_package))
        if len(installed_packages):
            # Found the Pip package info: this contains the version
            return installed_packages[0]["version"]
        else:
            # Pip package not found
            # This can happen because the package wasn't installed with Pip, but is available because it's importable
            return super(PythonPackageOnPip, self).get_installed_version(local_config)


###################################
# Some commonly used dependencies #
###################################

numpy_dependency = PythonPackageSystemwideInstall("numpy", "Numpy",
                                                  pip_package="numpy", yum_package="numpy", apt_package="python-numpy",
                                                  url="http://www.numpy.org/")
scipy_dependency = PythonPackageSystemwideInstall("scipy", "Scipy",
                                                  pip_package="scipy", yum_package="scipy", apt_package="python-scipy",
                                                  url="https://www.scipy.org/scipylib/")
theano_dependency = PythonPackageOnPip("theano", pip_package="Theano")
# We usually need h5py for reading/storing models
h5py_dependency = PythonPackageOnPip("h5py", pip_package="h5py")
keras_dependency = PythonPackageOnPip("keras", dependencies=[theano_dependency, h5py_dependency])
sklearn_dependency = PythonPackageOnPip(
    "sklearn", "Scikit-learn", pip_package="scikit-learn", dependencies=[numpy_dependency, scipy_dependency]
)
gensim_dependency = PythonPackageOnPip("gensim", "Gensim", dependencies=[numpy_dependency, scipy_dependency])


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
        super(BeautifulSoupDependency, self).__init__("bs4", pip_package="beautifulsoup4", name="Beautiful Soup")

    def import_package(self):
        return safe_import_bs4()

beautiful_soup_dependency = BeautifulSoupDependency()
