"""
Tools for Python library dependencies.

Provides superclasses for Python library dependencies and a selection of commonly used dependency instances.

"""
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
        try:
            __import__(self.package)
        except ImportError:
            probs.append("could not import %s" % self.package)
        return probs


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
    def __init__(self, package, name, pip_package=None, **kwargs):
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

        # Build a requirement set containing just the package we need
        requirement_set = RequirementSet(build_dir=build_prefix, src_dir=src_prefix, download_dir=None)
        requirement_set.add_requirement(InstallRequirement.from_line(self.pip_package))

        install_options = []
        global_options = []
        finder = PackageFinder(find_links=[], index_urls=["http://pypi.python.org/simple/"])

        requirement_set.prepare_files(finder, force_root_egg_info=False, bundle=False)
        # Run installation
        requirement_set.install(install_options, global_options)


###################################
# Some commonly used dependencies #
###################################

numpy_dependency = PythonPackageSystemwideInstall("numpy", "Numpy",
                                                  pip_package="numpy", yum_package="numpy", apt_package="python-numpy",
                                                  url="http://www.numpy.org/")
scipy_dependency = PythonPackageSystemwideInstall("scipy", "Scipy",
                                                  pip_package="scipy", yum_package="scipy", apt_package="python-scipy",
                                                  url="https://www.scipy.org/scipylib/")
