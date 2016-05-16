"""
Base classes for defining software dependencies for module types and routines for fetching them.

"""
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
        raise NotImplementedError

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

    def available(self):
        # Try calling check_runtime_dependencies() to see if anything's missing
        missing_deps = self.module.check_runtime_dependencies()
        if len(missing_deps):
            return False
        else:
            return True

    def installable(self):
        return False

    def installation_instructions(self):
        missing_deps = self.module.check_runtime_dependencies()
        # Collect messages from each missing dependency
        dep_messages = [
            "%s (for %s):\n  %s" % (
                dep_name, module_name, "\n  ".join(wrap(desc, width="100").splitlines())
            ) for dep_name, module_name, desc in missing_deps
        ]
        return """\
Some library dependencies are missing, but do not provide automatic installation.

%s
""" % "\n\n".join(dep_messages)


def check_and_install(deps, trust_downloaded_archives=False):
    """
    Check whether dependencies are available and try to install those that aren't. Returns a list of dependencies
    that can't be installed.

    """
    uninstallable = []
    for dep in deps:
        if not dep.available():
            # Haven't got this library
            # TODO Also check recursive deps
            if dep.installable():
                print "Installing %s" % dep.name
                dep.install(trust_downloaded_archives=trust_downloaded_archives)
                if not dep.available():
                    print "Ran installation routine for %s, but it's still not available" % dep.name
                    uninstallable.append(dep)
                else:
                    print "Installed"
            else:
                print "%s cannot be installed automatically" % dep.name
                instructions = dep.installation_instructions()
                if instructions:
                    print "\n".join("  %s" % line for line in instructions.splitlines())
                uninstallable.append(dep)
            print
    return uninstallable
