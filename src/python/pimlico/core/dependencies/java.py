import os
from subprocess import check_output, STDOUT, CalledProcessError

from pimlico import JAVA_LIB_DIR
from pimlico.core.dependencies.base import SoftwareDependency
from pimlico.core.external.java import call_java, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.utils.filesystem import new_filename, extract_from_archive
from pimlico.utils.web import download_file


class JavaDependency(SoftwareDependency):
    """
    Base class for Java library dependencies.

    In addition to the usual functionality provided by dependencies, subclasses of this provide contributions
    to the Java classpath in the form of directories of jar files.

    The instance has a set of representative Java classes that the checker will try to load to check whether
    the library is available and functional. It will also check that all jar files exist.

    Jar paths and class directory paths are assumed to be relative to the Java lib dir (lib/java).

    Subclasses should provide install().

    """
    def __init__(self, name, classes=[], jars=[], class_dirs=[]):
        super(JavaDependency, self).__init__(name)
        self.class_dirs = class_dirs
        self.jars = jars
        self.classes = classes

    def available(self):
        # Check that class dirs and jar files exist
        for dir in self.class_dirs:
            dir_path = os.path.join(JAVA_LIB_DIR, dir)
            if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                return False
        for jar_path in self.jars:
            if not os.path.exists(os.path.join(JAVA_LIB_DIR, jar_path)):
                return False
        # Check Java is available
        try:
            check_java()
        except DependencyError:
            return False
        # Try loading each of the classes specified
        for cls in self.classes:
            try:
                check_java_dependency(cls, classpath=":".join(self.get_classpath_components()))
            except (DependencyCheckerError, DependencyError):
                return False

    def installable(self):
        # By default, Java deps are installable, though subclasses may override this
        return True

    def get_classpath_components(self):
        return [os.path.join(JAVA_LIB_DIR, path) for path in self.jars + self.class_dirs]


class JavaJarsDependency(JavaDependency):
    """
    Simple way to define a Java dependency where the library is packaged up in a jar, or a series of jars.
    The jars should be given as a list of (name, url) pairs, where name is the filename the jar should have
    and url is a url from which it can be downloaded.

    URLs may also be given in the form "url->member", where url is a URL to a tar.gz or zip archive and member
    is a member to extract from the archive. If the type of the file isn't clear from the URL (i.e. if it doesn't
    have ".zip" or ".tar.gz" in it), specify the intended extension in the form "[ext]url->member", where ext is
    "tar.gz" or "zip".

    """
    def __init__(self, name, jar_urls, **kwargs):
        self.jar_urls = jar_urls
        super(JavaJarsDependency, self).__init__(name, jars=[j for (j, url) in jar_urls], **kwargs)

    def install(self, trust_downloaded_archives=False):
        downloaded_archives = {}

        for jar_name, jar_url in self.jar_urls:
            if not os.path.exists(os.path.join(JAVA_LIB_DIR, jar_name)):
                if "->" in jar_url:
                    # Member to extract from an archive
                    archive_url, __, member = jar_url.partition("->")
                    print "Getting %s from %s" % (member, archive_url)
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
                            print "Reusing archive file %s and assuming it's come from %s" % \
                                  (archive_filename, archive_url)
                        else:
                            # Download the archive
                            print "Downloading %s from %s" % (archive_filename, archive_url)
                            download_file(archive_url, archive_filename)
                            # Don't download the same archive again if we need it multiple times
                            downloaded_archives[archive_url] = archive_filename

                    # Extract the member from the archive
                    extract_from_archive(archive_filename, member, JAVA_LIB_DIR)
                    print "Extracted %s" % member
                else:
                    # Download the jar file to the Java lib dir
                    print "Downloading %s from %s" % (jar_name, jar_url)
                    download_file(jar_url, os.path.join(JAVA_LIB_DIR, jar_name))

        # Delete any archives we downloaded
        for filename in downloaded_archives.values():
            os.remove(filename)


def check_java_dependency(class_name, classpath=None):
    """
    Utility to check that a java class is able to be loaded.

    """
    # First check that the dependency checker itself can be loaded
    out, err, code = call_java("pimlico.core.DependencyChecker", classpath=classpath)
    if code != 0:
        raise DependencyCheckerError(
            "could not load Java dependency checker. Have you compiled the Pimlico java core? %s" % (err or "")
        )

    out, err, code = call_java("pimlico.core.DependencyChecker", [class_name], classpath=classpath)
    if code != 0:
        raise DependencyError("could not load Java class %s. Have you compiled the relevant Java module?" % class_name,
                              stderr=err, stdout=out)


def check_java():
    """
    Check that the JVM executable can be found. Raises a DependencyError if it can't be found or can't
    be run.

    """
    try:
        check_output(["java", "-version"], stderr=STDOUT)
    except CalledProcessError, e:
        # If there was an error running this, Java was not found
        raise DependencyError("java executable could not be run: %s" % e.output)


def get_classpath(deps):
    """
    Given a list of JavaDependency subclass instances, returns all the components of the classpath that will
    make sure that the dependencies are available as a list. Get the full classpath by ":".join(x) on the list.

    """
    return list(set([dep.get_classpath_components() for dep in deps]))
