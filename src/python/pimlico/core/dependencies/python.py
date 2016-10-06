"""
Tools for Python library dependencies.

Provides superclasses for Python library dependencies and a selection of commonly used dependency instances.

"""
import copy
import sys
from traceback import format_exception_only

from pimlico.core.dependencies.base import SoftwareDependency


class PythonPackageDependency(SoftwareDependency):
    """
    Base class for Python dependencies. Provides import checks, but no installation routines. Subclasses should
    either provide install() or installation_instructions().

    """
    def __init__(self, package, name, **kwargs):
        super(PythonPackageDependency, self).__init__(name, **kwargs)
        self.package = package

    def problems(self):
        probs = super(PythonPackageDependency, self).problems()
        # Make a fresh start on trying to import the module, removing it from sys.modules if it's already been imported
        # If we don't do this, we might not get the same error the second time we call this
        removed_modules = []
        for mod_name in copy.copy(sys.modules):
            if mod_name.startswith(self.package):
                removed_modules.append((mod_name, sys.modules[mod_name]))
                del sys.modules[mod_name]

        try:
            self.import_package()
        except ImportError, e:
            e_type, e_value, __ = sys.exc_info()
            error = " // ".join([e.strip(" \n") for e in format_exception_only(e_type, e_value)])
            probs.append("could not import %s (%s)" % (self.package, error))
        finally:
            # If we removed any modules from sys.modules before the import and they've not been added in by the import,
            #  put them back again now
            for mod_name, mod_val in removed_modules:
                if mod_name not in sys.modules:
                    sys.modules[mod_name] = mod_val
        return probs

    def import_package(self):
        """
        Try importing package_name. By default, just uses `__import__`. Allows subclasses to allow for
        special import behaviour.

        Should raise an `ImportError` if import fails.

        """
        return __import__(self.package)

    def get_installed_version(self):
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
        return super(PythonPackageDependency, self).get_installed_version()

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

    def install(self, trust_downloaded_archives=False):
        from pip.index import PackageFinder
        from pip.req import InstallRequirement, RequirementSet
        from pip.locations import build_prefix, src_prefix

        # Enable verbose output
        # NB: This only works on old versions of Pip
        # TODO Implement equivalent for newer versions
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

    def __repr__(self):
        return "PythonPackageOnPip<%s%s>" % (self.name, (" (%s)" % self.package) if self.package != self.name else "")

    def get_installed_version(self):
        from pip.commands.show import search_packages_info
        # Use Pip to get the version number of the installed version
        installed_packages = list(search_packages_info(self.pip_package))
        if len(installed_packages):
            # Found the Pip package info: this contains the version
            return installed_packages[0]["version"]
        else:
            # Pip package not found
            # This can happen because the package wasn't installed with Pip, but is available because it's importable
            return super(PythonPackageOnPip, self).get_installed_version()


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
keras_dependency = PythonPackageOnPip("keras", dependencies=[theano_dependency])
