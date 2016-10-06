"""
Base classes for defining software dependencies for module types and routines for fetching them.

"""
import subprocess

from pimlico.core.dependencies.versions import unknown_software_version


class SoftwareDependency(object):
    """
    Base class for all Pimlico module software dependencies.

    """
    def __init__(self, name, url=None, dependencies=None):
        self.url = url
        self.name = name
        self._dependencies = dependencies or []

    def available(self):
        """
        Return True if the dependency is satisfied, meaning that the software/library is installed and ready to
        use.

        """
        return len(self.problems()) == 0

    def problems(self):
        """
        Returns a list of problems standing in the way of the dependency being available. If the list is empty,
        the dependency is taken to be installed and ready to use.

        Overriding methods should call super method.

        """
        return sum([dep.problems() for dep in self.dependencies()], [])

    def installable(self):
        """
        Return True if it's possible to install this library automatically. If False, the user will have to install
        it themselves. Instructions for doing this may be provided by installation_instructions(), which will only
        generally be called if installable() returns False.

        This might be the case, for example, if the software is not available to download freely, or if it requires
        a system-wide installation.

        """
        raise NotImplementedError

    def installation_instructions(self):
        """
        Where a dependency can't be installed programmatically, we typically want to be able to output instructions
        for the user to tell them how to go about doing it themselves. Any subclass that doesn't provide an automatic
        installation routine should override this to provide instructions.

        """
        return ""

    def dependencies(self):
        """
        Returns a list of instances of :class:SoftwareDependency subcalsses representing this library's own
        dependencies. If the library is already available, these will never be consulted, but if it is to be
        installed, we will check first that all of these are available (and try to install them if not).

        """
        return self._dependencies

    def install(self, trust_downloaded_archives=False):
        """
        Should be overridden by any subclasses whose library is automatically installable. Carries out the actual
        installation.

        You may assume that all dependencies returned by :method:dependencies have been satisfied prior to
        calling this.

        """
        raise NotImplementedError

    def __repr__(self):
        return "%s<%s>" % (type(self).__name__, self.name)

    def all_dependencies(self):
        """
        Recursively fetch all dependencies of this dependency (not including itself).

        """
        return self.dependencies() + sum([dep.all_dependencies() for dep in self.dependencies()], [])

    def get_installed_version(self):
        """
        If available() returns True, this method should return a SoftwareVersion object (or subclass) representing
        the software's version.

        The base implementation returns an object representing an unknown version number.

        If available() returns False, the behaviour is undefined and may raise an error.
        """
        return unknown_software_version

    def __hash__(self):
        return 0


class SystemCommandDependency(SoftwareDependency):
    """
    Dependency that tests whether a command is available on the command line.
    Generally requires system-wide installation.

    """
    def __init__(self, name, test_command, **kwargs):
        super(SystemCommandDependency, self).__init__(name, **kwargs)
        self.test_command = test_command

    def installable(self):
        """
        Usually not automatically installable
        """
        return False

    def problems(self):
        problems = super(SystemCommandDependency, self).problems()
        # Try running the test command
        command = self.test_command.split()
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            problems.append("Command '%s' failed: %s" % (self.test_command, e.output))
        return problems


class InstallationError(Exception):
    pass


def check_and_install(deps, trust_downloaded_archives=False):
    """
    Check whether dependencies are available and try to install those that aren't. Returns a list of dependencies
    that can't be installed.

    """
    from pimlico.utils.format import title_box
    uninstallable = []
    installed = []
    for dep in deps:
        if not dep.available():
            # Haven't got this library
            # First check whether there are recursive deps we can install
            check_and_install(dep.dependencies(), trust_downloaded_archives=trust_downloaded_archives)
            # Now check again whether the library's available
            if not dep.available():
                print "\n%s" % title_box(dep.name)
                if dep.installable():
                    try:
                        install(dep, trust_downloaded_archives=trust_downloaded_archives)
                    except InstallationError, e:
                        print "Could not install %s:\n%s" % (dep.name, e)
                        uninstallable.append(dep)
                    else:
                        print "Installed"
                        installed.append(dep.name)
                else:
                    print "%s cannot be installed automatically" % dep.name
                    instructions = dep.installation_instructions()
                    if instructions:
                        print "\n".join("  %s" % line for line in instructions.splitlines())
                    uninstallable.append(dep)
                print

    if installed:
        print "Installed: %s" % ", ".join(installed)
    if uninstallable:
        print "Could not install: %s" % ", ".join(dep.name for dep in uninstallable)
    return uninstallable


def install(dep, trust_downloaded_archives=False):
    if not dep.installable():
        raise InstallationError("%s is not installable" % dep.name)
    # Collect any recursive dependencies that need to be installed first
    all_deps = recursive_deps(dep)
    all_deps.append(dep)
    # Only need to include deps not already available
    to_install = [dep for dep in all_deps if not dep.available()]
    # Check everything is installable
    uninstallable = [dep for dep in to_install if not dep.installable()]
    if uninstallable:
        raise InstallationError("could not install %s, as some of its dependencies are unavailable and not "
                                "automatically installable: %s" % (dep.name, ", ".join(d.name for d in uninstallable)))
    # Install each of the prerequisites
    for sub_dep in to_install:
        # Check that this is still not available, in case installing one of the others has provided incidentally
        if not sub_dep.available():
            extra_message = "" if sub_dep is dep else " (prerequisite for %s)" % dep.name
            print "Installing %s%s" % (sub_dep.name, extra_message)
            sub_dep.install(trust_downloaded_archives=trust_downloaded_archives)
            # Check the installation worked
            remaining_problems = sub_dep.problems()
            if remaining_problems:
                raise InstallationError(
                    "Ran installation routine for %s, but it's still not available due to the following " \
                    "problems:\n%s" % (sub_dep.name, "\n".join("  - %s" % p for p in remaining_problems)))


def install_dependencies(pipeline, modules=None, trust_downloaded_archives=True):
    """
    Install depedencies for pipeline modules

    :param pipeline:
    :param modules: list of module names, or None to install for all
    :return:
    """
    from pimlico.core.config import get_dependencies

    if modules is None:
        modules = pipeline.modules

    deps = get_dependencies(pipeline, modules)
    check_and_install(deps, trust_downloaded_archives=trust_downloaded_archives)


def recursive_deps(dep):
    """
    Collect all recursive dependencies of this dependency. Does a depth-first search so that everything comes
    later in the list than things it depends on.

    """
    all_deps = []
    for sub_dep in dep.dependencies():
        all_deps.extend(recursive_deps(sub_dep))
        all_deps.append(sub_dep)
    return all_deps
