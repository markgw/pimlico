# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function

import shutil

import sys

import os
from subprocess import check_output, STDOUT, CalledProcessError

from pimlico.core.dependencies.licenses import BSD, MIT

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_JAR_DIR
from pimlico.core.dependencies.base import SoftwareDependency, InstallationError, Any
from pimlico.core.external.java import call_java, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.utils.core import remove_duplicates
from pimlico.utils.filesystem import new_filename, extract_from_archive
from pimlico.utils.web import download_file


class JavaDependency(SoftwareDependency):
    """
    Base class for Java library dependencies.

    In addition to the usual functionality provided by dependencies, subclasses of this provide contributions
    to the Java classpath in the form of directories of jar files.

    The instance has a set of representative Java classes that the checker will try to load to check whether
    the library is available and functional. It will also check that all jar files exist.

    Jar paths and class directory paths are assumed to be relative to the Java lib dir (lib/java), unless they
    are absolute paths.

    Subclasses should provide install() and override installable() if it's possible to install them automatically.

    """
    def __init__(self, name, classes=[], jars=[], class_dirs=[], **kwargs):
        super(JavaDependency, self).__init__(name, **kwargs)
        self.class_dirs = class_dirs
        self.jars = jars
        self.classes = classes

    def problems(self, local_config):
        probs = super(JavaDependency, self).problems(local_config)
        classpath_problem = False
        # Check that class dirs and jar files exist
        for dir in self.class_dirs:
            dir_path = os.path.join(JAVA_LIB_DIR, dir)
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                probs.append("class directory %s does not exist" % dir_path)
                classpath_problem = True
        for jar_name in self.jars:
            jar_path = os.path.join(JAVA_LIB_DIR, jar_name)
            if not os.path.exists(jar_path):
                probs.append("jar file %s does not exist" % jar_path)
                classpath_problem = True
        # Check Java is available
        try:
            check_java()
        except DependencyError:
            probs.append("Java is not installed")
        # If there's been a problem above with something on the classpath, don't try
        # loading the classes, as you end up with confusing error messages saying a
        # class can't be loaded when you've already said a library is missing
        if not classpath_problem:
            # Try loading each of the classes specified
            classpath = ":".join(self.get_classpath_components())
            for cls in self.classes:
                try:
                    check_java_dependency(cls, classpath=classpath)
                except DependencyCheckerError:
                    probs.append("unable to load Java dependency checker to check classes are loadable")
                except DependencyError as e:
                    # Usually, the first line is enough to tell what the error was (start of stack trace)
                    error_output = e.stderr.partition("\n")[0].strip()
                    extra_message = ". Loader output: %s" % error_output if error_output else ""
                    probs.append("could not load Java class %s (classpath=%s)%s" % (cls, classpath, extra_message))
        return probs

    def installable(self):
        # By default, Java deps are not installable, though subclasses may override this if they provide install()
        return False

    def jar_paths(self, local_config):
        """ Absolute paths to the jars """
        return [path if os.path.isabs(path) else os.path.join(JAVA_LIB_DIR, path) for path in self.all_jars(local_config)]

    def all_jars(self, local_config):
        """ Get all jars, including from dependencies """
        jars = list(self.jars)
        for dep in self.dependencies():
            if isinstance(dep, JavaDependency):
                jars.extend(dep.all_jars())
            elif isinstance(dep, Any):
                av_dep = dep.get_available_option(local_config)
                if av_dep is not None and isinstance(av_dep, JavaDependency):
                    jars.extend(av_dep.all_jars(local_config))
        return jars

    def _get_classpath_components_non_recursive(self):
        return [path if os.path.isabs(path) else os.path.join(JAVA_LIB_DIR, path)
                for path in self.jars + self.class_dirs]

    def get_classpath_components(self):
        # Include our own class dirs and jars, as well as those of any java dependencies
        java_deps = [dep for dep in self.all_dependencies() if isinstance(dep, JavaDependency)]
        java_deps.insert(0, self)
        return remove_duplicates(
            sum((dep._get_classpath_components_non_recursive() for dep in java_deps), [])
        )

    def __hash__(self):
        return 0

    def __eq__(self, other):
        return isinstance(other, JavaDependency) and \
               set(self.classes) == set(other.classes) and \
               set(self.jars) == set(other.jars) and \
               set(self.class_dirs) == set(other.class_dirs)


class JavaJarsDependency(JavaDependency):
    """
    Simple way to define a Java dependency where the library is packaged up in a jar, or a series of jars.
    The jars should be given as a list of (name, url) pairs, where name is the filename the jar should have
    and url is a url from which it can be downloaded.

    URLs may also be given in the form "url->member", where url is a URL to a tar.gz or zip archive and member
    is a member to extract from the archive. If the type of the file isn't clear from the URL (i.e. if it doesn't
    have ".zip" or ".tar.gz" in it), specify the intended extension in the form "[ext]url->member", where ext is
    "tar.gz" or "zip".

    If multiple jars come from the same URL (i.e. the same archive), it will only be downloaded once.

    """
    def __init__(self, name, jar_urls, **kwargs):
        self.jar_urls = jar_urls
        super(JavaJarsDependency, self).__init__(name, jars=[j for (j, url) in jar_urls], **kwargs)

    def installable(self):
        return True

    def install(self, local_config, trust_downloaded_archives=False):
        downloaded_archives = {}
        archive_files = {}
        archives_to_download = []
        to_download = []
        # Only output the "reusing" message once per file
        reusing = []

        for jar_name, jar_url in self.jar_urls:
            if not os.path.exists(os.path.join(JAVA_LIB_DIR, jar_name)):
                if "->" in jar_url:
                    # Member to extract from an archive
                    archive_url, __, member = jar_url.partition("->")
                    # Check whether we've already downloaded this archive and don't do it again if so
                    if archive_url in downloaded_archives:
                        archive_filename = downloaded_archives[archive_url]
                    else:
                        # Work out a filename to save the archive as
                        archive_name = archive_url.rpartition("/")[2].partition("?")[0]
                        # Check whether an explicit extension was given
                        if "[" in archive_url and "]" in archive_url:
                            ext, __, archive_url = archive_url.partition("]")
                            ext = ext.strip("[")
                        else:
                            # Otherwise, it's expected to be clear from the URL
                            ext = os.path.splitext(archive_name)[1]

                        if len(archive_name) == 0:
                            # URL doesn't provide an obvious name: make one up
                            archive_name = new_filename(JAVA_LIB_DIR, "downloaded.%s" % ext)

                        archive_filename = os.path.join(JAVA_LIB_DIR, archive_name)

                        if trust_downloaded_archives and os.path.exists(archive_filename):
                            # If we've been told to rely on previously downloaded archives to be the right thing,
                            # reuse this archive
                            if archive_filename not in reusing:
                                print("Reusing archive file %s (as %s)" % \
                                      (archive_filename, archive_url))
                                reusing.append(archive_filename)
                        else:
                            # Download the archive
                            archives_to_download.append((archive_url, archive_filename))
                            # Don't download the same archive again if we need it multiple times
                            downloaded_archives[archive_url] = archive_filename

                    # Extract the member from the archive
                    archive_files.setdefault(archive_filename, []).append(member)
                else:
                    # Download the jar file to the Java lib dir
                    to_download.append((jar_url, jar_name))

        # Download all archives we need
        for archive_url, archive_filename in archives_to_download:
            print("Downloading %s from %s" % (archive_filename, archive_url))
            try:
                download_file(archive_url, archive_filename)
            except Exception as e:
                raise InstallationError("could not download archive from '{}': {}".format(archive_url, e))

        # Got all the archives, extract the required members
        for archive_filename, members in archive_files.items():
            extract_from_archive(archive_filename, members, JAVA_LIB_DIR, preserve_dirs=False)
            print("Extracted %s" % ", ".join(members))

        for jar_url, jar_name in to_download:
            print("Downloading %s from %s" % (jar_name, jar_url))
            download_file(jar_url, os.path.join(JAVA_LIB_DIR, jar_name))

        # Delete any archives we downloaded
        for filename in downloaded_archives.values():
            os.remove(filename)


class PimlicoJavaLibrary(JavaDependency):
    """
    Special type of Java dependency for the Java libraries provided with Pimlico. These are packages up in jars
    and stored in the build dir.

    """
    def __init__(self, name, classes=[], additional_jars=[]):
        super(PimlicoJavaLibrary, self).__init__(
            "%s Pimlico library" % name.capitalize(),
            jars=[os.path.join(JAVA_BUILD_JAR_DIR, "%s.jar" % name)] + additional_jars,
            classes=classes
        )


def check_java_dependency(class_name, classpath=None):
    """
    Utility to check that a java class is able to be loaded.

    """
    # First check that the dependency checker itself can be loaded
    out, err, code = call_java("pimlico.core.DependencyChecker", classpath=classpath)
    if code != 0:
        raise DependencyCheckerError(
            "could not load Java dependency checker. Problem with Pimlico setup. %s" % (err or "")
        )

    out, err, code = call_java("pimlico.core.DependencyChecker", [class_name], classpath=classpath)
    if code != 0:
        raise DependencyError("could not load Java class %s" % class_name, stderr=err, stdout=out)


def check_java():
    """
    Check that the JVM executable can be found. Raises a DependencyError if it can't be found or can't
    be run.

    """
    try:
        check_output(["java", "-version"], stderr=STDOUT)
    except CalledProcessError as e:
        # If there was an error running this, Java was not found
        raise DependencyError("java executable could not be run: %s" % e.output)


def get_classpath(deps, as_list=False):
    """
    Given a list of JavaDependency subclass instances, returns all the components of the classpath that will
    make sure that the dependencies are available.

    If as_list=True, returned as a list.
    Get the full classpath by ":".join(x) on the list.
    If as_list=False, returns classpath string.

    """
    components = list(set(sum((dep.get_classpath_components() for dep in deps if isinstance(dep, JavaDependency)), [])))
    if as_list:
        return components
    else:
        return ":".join(components)


def get_module_classpath(module):
    """
    Builds a classpath that includes all of the classpath elements specified by Java dependencies of the given
    module. These include the dependencies from get_software_dependencies() and also any dependencies of the
    datatype.

    Used to ensure that Java modules that depend on particular jars or classes get all of those files included
    on their classpath when Java is run.

    """
    deps = module.get_software_dependencies()
    deps.extend(module.get_input_software_dependencies())
    return get_classpath(deps)


argparse4j_dependency = JavaJarsDependency(
    "argparse4j",
    jar_urls=[("argparse4j.jar", "http://sourceforge.net/projects/argparse4j/files/latest/download?source=files")],
    homepage_url="https://argparse4j.github.io/", license=MIT,
)


class Py4JSoftwareDependency(JavaDependency):
    """
    Java component of Py4J. Use this one as the main dependency, as it depends on the Python component and will
    install that first if necessary.

    """
    def __init__(self):
        super(Py4JSoftwareDependency, self).__init__("Py4J Java component", classes=["py4j.Gateway"],
                                                     homepage_url="https://www.py4j.org/",
                                                     license=BSD)
        self._extra_jars = []

    def dependencies(self):
        # Must have the Python component installed first
        from .python import PythonPackageOnPip
        return super(Py4JSoftwareDependency, self).dependencies() + [
            PythonPackageOnPip("py4j", name="Py4J Python component", homepage_url="https://www.py4j.org/", license=BSD)]

    def __get_jars(self):
        try:
            from py4j.version import __version__ as py4j_version
        except ImportError:
            # python-side package isn't installed, can't work out what jar name should be
            return self._extra_jars + ["py4jx.y.jar"]
        else:
            return self._extra_jars + ["py4j%s.jar" % py4j_version]

    def __set_jars(self, jars):
        self._extra_jars = jars

    jars = property(__get_jars, __set_jars)

    def installable(self):
        return True

    def install(self, local_config, trust_downloaded_archives=False):
        # We know Py4J (Python component) is already installed
        # If it's installed system-wide, this is tricky, as we don't know where it is
        jar_name = self.jars[0]
        # Get hold of the jar file, which should have been installed along with Py4J and put it in our java lib dir
        try:
            import py4j
        except ImportError:
            raise InstallationError("can't import py4j package: something must have gone wrong in installation")

        jar_path = os.path.join(sys.prefix, "share", "py4j", jar_name)
        if not os.path.exists(jar_path):
            raise InstallationError("py4j importable in Python, but jar file %s doesn't exist. Locate it and copy to "
                                    "%s" % (jar_path, JAVA_LIB_DIR))
        shutil.copy2(jar_path, JAVA_LIB_DIR)


py4j_dependency = Py4JSoftwareDependency()
