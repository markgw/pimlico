"""
Base classes for defining software dependencies for module types and routines for fetching them.

"""
import subprocess
from textwrap import wrap


class SoftwareDependency(object):
    """
    Base class for all Pimlico module software dependencies.

    """
    def __init__(self, name, url=None):
        self.url = url
        self.name = name

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
        return []

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
        return []

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


class LegacyModuleDependencies(SoftwareDependency):
    """
    Wrapper for modules that still use the old check_runtime_dependencies() method to specify their dependencies.
    A single instance of this represents all of a module's dependencies. None of them are automatically installable,
    but notes/installation instructions are provided.

    This will be removed when the deprecated check_runtime_dependencies() method is removed.

    """
    def __init__(self, module):
        super(LegacyModuleDependencies, self).__init__("dependencies for module '%s'" % module.module_name)
        self.module = module

    def problems(self):
        probs = super(LegacyModuleDependencies, self).problems()
        # Try calling check_runtime_dependencies() to see if anything's missing
        missing_deps = self.module.check_runtime_dependencies()
        for dep_name, module_name, desc in missing_deps:
            probs.append("module '%s' is missing dependency '%s': %s" % (module_name, dep_name, desc))
        return probs

    def installable(self):
        return False

    def installation_instructions(self):
        missing_deps = self.module.check_runtime_dependencies()
        # Collect messages from each missing dependency
        dep_messages = [
            "%s (for %s):\n  %s" % (
                dep_name, module_name, "\n  ".join(wrap(desc, width=100))
            ) for dep_name, module_name, desc in missing_deps
        ]
        return """\
Some library dependencies are missing, but do not provide automatic installation.

%s
""" % "\n\n".join(dep_messages)

    def __repr__(self):
        return "LegacyModuleDependencies<%s>" % self.module.module_name


class LegacyDatatypeDependencies(SoftwareDependency):
    """
    Wrapper for datatypes that still use the old check_runtime_dependencies() method to specify their dependencies.
    A single instance of this represents all of a datatype's dependencies. None of them are automatically installable,
    but notes/installation instructions are provided.

    Can also be applied to datatypes, which also have a check_runtime_dependencies() method.

    This will be removed when the deprecated check_runtime_dependencies() method is removed.

    """
    def __init__(self, datatype):
        super(LegacyDatatypeDependencies, self).__init__("dependencies for datatype '%s'" % datatype.datatype_name)
        self.datatype = datatype

    def problems(self):
        probs = super(LegacyDatatypeDependencies, self).problems()
        # Try calling check_runtime_dependencies() to see if anything's missing
        missing_deps = self.datatype.check_runtime_dependencies()
        for dep_name, desc in missing_deps:
            probs.append("datatype '%s' is missing dependency '%s': %s" % (self.datatype.datatype_name, dep_name, desc))
        return probs

    def installable(self):
        return False

    def installation_instructions(self):
        missing_deps = self.datatype.check_runtime_dependencies()
        # Collect messages from each missing dependency
        dep_messages = [
            "%s (for %s):\n  %s" % (
                dep_name, self.datatype.datatype_name, "\n  ".join(wrap(desc, width="100").splitlines())
            ) for dep_name, desc in missing_deps
            ]
        return """\
Some library dependencies are missing, but do not provide automatic installation.

%s
""" % "\n\n".join(dep_messages)

    def __repr__(self):
        return "LegacyDatatypeDependencies<%s>" % self.datatype.datatype_name


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
            print title_box(dep.name)
            # Haven't got this library
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

    if not installed and not uninstallable:
        print "All dependencies satisfied"
    else:
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
