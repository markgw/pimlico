# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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

    def available(self, local_config):
        """
        Return True if the dependency is satisfied, meaning that the software/library is installed and ready to
        use.

        """
        return len(self.problems(local_config)) == 0

    def problems(self, local_config):
        """
        Returns a list of problems standing in the way of the dependency being available. If the list is empty,
        the dependency is taken to be installed and ready to use.

        Overriding methods should call super method.

        """
        return sum([dep.problems(local_config) for dep in self.dependencies()], [])

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

        You may also provide this even if the class does provide automatic installation. For example, you might
        want to provide instructions for other ways to install the software, like a system-wide install. This
        instructions will be shown together with missing dependency information.

        """
        return ""

    def installation_notes(self):
        """
        If this returns a non-empty string, the message will be output together with
        the information that the dependency is not available, before the user is given
        the option of installing it automatically (or told that it can't be). This
        is useful where information about a dependency should always be displayed, not
        just in cases where automatic installation isn't possible.

        For example, you might need to include warnings about potential installation
        difficulties, license information, sources of additional information about
        the software, and so on.

        """
        return ""

    def dependencies(self):
        """
        Returns a list of instances of :class:SoftwareDependency subclasses representing this library's own
        dependencies. If the library is already available, these will never be consulted, but if it is to be
        installed, we will check first that all of these are available (and try to install them if not).

        """
        return self._dependencies

    def install(self, local_config, trust_downloaded_archives=False):
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
        immediate_deps = self.dependencies()
        return sum([dep.all_dependencies() for dep in immediate_deps], []) + immediate_deps

    def get_installed_version(self, local_config):
        """
        If available() returns True, this method should return a SoftwareVersion object (or subclass) representing
        the software's version.

        The base implementation returns an object representing an unknown version number.

        If available() returns False, the behaviour is undefined and may raise an error.
        """
        return unknown_software_version

    def __hash__(self):
        return 0


class Any(SoftwareDependency):
    """
    A collection of dependency requirements of which at least one must be
    available. The first in the list that is installable is treated as the
    default and used for automatic installation.

    """
    def __init__(self, name, dependency_options, *args, **kwargs):
        super(Any, self).__init__(name, *args, **kwargs)
        self.dependency_options = dependency_options

    def available(self, local_config):
        return any(dep.available(local_config) for dep in self.dependency_options)

    def problems(self, local_config):
        if self.available(local_config):
            # At least one of the dependencies is available, so we report no problems
            return []
        else:
            # No dependency is satisfied: report the problems from every one, even
            # though only one of them needs to be fixed
            return sum([dep.problems(local_config) for dep in self.dependency_options], [])

    def installable(self):
        return self.get_installation_candidate() is not None

    def get_installation_candidate(self):
        """
        Returns the first dependency of the multiple possibilities that is
        automatically installable, or None if none of them are.

        """
        for dep in self.dependency_options:
            if dep.installable():
                return dep
        else:
            return None

    def get_available_option(self, local_config):
        """ If one of the options is available, return that one. Otherwise return None. """
        for dep in self.dependency_options:
            if dep.available(local_config):
                return dep
        return None

    def dependencies(self):
        candidate = self.get_installation_candidate()
        if candidate is None:
            return []
        else:
            return candidate.dependencies()

    def install(self, local_config, trust_downloaded_archives=False):
        """
        Installs the dependency given by :method:`get_installation_candidate`, if any.
        Ideally, we should provide a way to select which of the options should be
        installed. However, until we've worked out the best way to do this, the default
        option is always installed. The user may install another option manually and
        that will be used.

        """
        candidate = self.get_installation_candidate()
        if candidate is None:
            raise NotImplementedError("dependency is not installable")
        candidate.install(local_config, trust_downloaded_archives=trust_downloaded_archives)

    def installation_notes(self):
        opt_notes = [d.installation_notes().strip() for d in self.dependency_options]
        opt_notes = [d for d in opt_notes if len(d) > 0]
        return u"\n\n".join(["Only one of these needs to be installed"]+opt_notes)

    def __repr__(self):
        return "({})".format(" | ".join(repr(d) for d in self.dependency_options))


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

    def problems(self, local_config):
        problems = super(SystemCommandDependency, self).problems(local_config)
        # Try running the test command
        command = self.test_command.split()
        try:
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError, e:
            problems.append("Command '%s' failed: %s" % (self.test_command, e.output))
        except OSError, e:
            problems.append("Command '%s' failed: %s" % (self.test_command, e))
        return problems


class InstallationError(Exception):
    pass


def check_and_install(deps, local_config, trust_downloaded_archives=False):
    """
    Check whether dependencies are available and try to install those that aren't. Returns a list of dependencies
    that can't be installed.

    """
    from pimlico.utils.format import title_box
    uninstallable = []
    installed = []

    # Remove any dependencies that are already available at the beginning
    # We should silently pass over them
    deps = [d for d in deps if not d.available(local_config)]

    for dep in deps:
        print ", ".join("%s (%s)" % (d.name, "Y" if d.available(local_config) else "N") for d in deps)
        if dep.available(local_config):
            print "%s became available while installing other dependencies" % dep.name
        else:
            # Haven't got this library
            # First check whether there are recursive deps we can install
            subdeps_uninstallable = check_and_install(dep.dependencies(), local_config, trust_downloaded_archives=trust_downloaded_archives)
            uninstallable.extend(subdeps_uninstallable)
            # Now check again whether the library's available
            if not dep.available(local_config):
                print "\n%s" % title_box(dep.name)
                if dep.installable():
                    try:
                        install(dep, local_config, trust_downloaded_archives=trust_downloaded_archives)
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
                        print "Installation instructions:\n"
                        print "\n".join("  %s" % line for line in instructions.splitlines())
                    else:
                        print "No installation instructions are available"
                    uninstallable.append(dep)
                print
            else:
                print "%s became available while installing sub-dependencies" % dep.name

    if installed:
        print "Installed: %s" % ", ".join(installed)
    if uninstallable:
        print "Could not install: %s" % ", ".join(dep.name for dep in uninstallable)
    print
    return uninstallable


def install(dep, local_config, trust_downloaded_archives=False):
    if not dep.installable():
        raise InstallationError("%s is not installable" % dep.name)
    # Collect any recursive dependencies that need to be installed first
    all_deps = recursive_deps(dep)
    all_deps.append(dep)
    # Only need to include deps not already available
    to_install = [dep for dep in all_deps if not dep.available(local_config)]
    # Check everything is installable
    uninstallable = [dep for dep in to_install if not dep.installable()]
    if uninstallable:
        raise InstallationError("could not install %s, as some of its dependencies are unavailable and not "
                                "automatically installable: %s" % (dep.name, ", ".join(d.name for d in uninstallable)))
    # Install each of the prerequisites
    for sub_dep in to_install:
        # Check that this is still not available, in case installing one of the others has provided incidentally
        if not sub_dep.available(local_config):
            extra_message = "" if sub_dep is dep else " (prerequisite for %s)" % dep.name
            print "Installing %s%s" % (sub_dep.name, extra_message)
            sub_dep.install(local_config, trust_downloaded_archives=trust_downloaded_archives)
            # Check the installation worked
            remaining_problems = sub_dep.problems(local_config)
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
    check_and_install(deps, pipeline.local_config, trust_downloaded_archives=trust_downloaded_archives)


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
