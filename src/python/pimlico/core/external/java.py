from subprocess import Popen, PIPE

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_DIR
from pimlico.core.modules.base import DependencyError


def call_java(class_name, args=[]):
    classpath = ":".join(["%s/*" % JAVA_LIB_DIR, JAVA_BUILD_DIR])
    # May in future want to allow the path to the java executable to be specified in local config
    process = Popen(["java", "-cp", classpath, class_name] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    stdout_data, stderr_data = process.communicate()
    return stdout_data, stderr_data, process.returncode


def start_java_process(class_name, args=[]):
    classpath = ":".join(["%s/*" % JAVA_LIB_DIR, JAVA_BUILD_DIR])
    # May in future want to allow the path to the java executable to be specified in local config
    process = Popen(["java", "-cp", classpath, class_name] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    return process


def check_java_dependency(class_name):
    """
    Utility to check that a java class is able to be loaded.

    """
    # First check that the dependency checker itself can be loaded
    out, err, code = call_java("pimlico.core.DependencyChecker")
    if code != 0:
        raise DependencyCheckerError("could not load Java dependency checker. Have you compiled the Pimlico java core? "
                                     "%s" % (err or ""))

    out, err, code = call_java("pimlico.core.DependencyChecker", [class_name])
    if code != 0:
        raise DependencyError("could not load Java class %s. Have you compiled the relevant Java module?" % class_name)


class DependencyCheckerError(Exception):
    pass
