import Queue
from collections import deque
import os
import time
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_DIR
from pimlico.core.modules.base import DependencyError
from py4j.java_gateway import JavaGateway, GatewayParameters, OutputConsumer, ProcessConsumer

CLASSPATH = ":".join(["%s/*" % JAVA_LIB_DIR, JAVA_BUILD_DIR])


def call_java(class_name, args=[]):
    # May in future want to allow the path to the java executable to be specified in local config
    process = Popen(["java", "-cp", CLASSPATH, class_name] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    stdout_data, stderr_data = process.communicate()
    return stdout_data, stderr_data, process.returncode


def start_java_process(class_name, args=[], wait=0.1):
    # May in future want to allow the path to the java executable to be specified in local config
    cmd = ["java", "-cp", CLASSPATH, class_name] + args
    process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)

    # Wait a mo for it to get started
    time.sleep(wait)
    if process.poll() is not None:
        if process.returncode == 0:
            raise JavaProcessError("java process exited immediately with return code 0: %s (ran: %s)" %
                                   (process.stderr.read(), " ".join(cmd)))
        else:
            raise JavaProcessError("java process failed with return code %d: %s (ran: %s)" %
                                   (process.returncode, process.stderr.read(), " ".join(cmd)))
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


class Py4JInterface(object):
    def __init__(self, gateway_class, port=None, python_port=None, gateway_args=[]):
        self.python_port = python_port
        self.gateway_args = gateway_args
        self.gateway_class = gateway_class
        self.port = port

        self.process = None
        self.gateway = None

    def start(self):
        """
        Start a Py4J gateway server in the background on the given port, which will then be used for
        communicating with the Java app.

        If a port has been given, it is assumed that the gateway accepts a --port option.
        Likewise with python_port and a --python-port option.

        """
        args = list(self.gateway_args)
        gateway_kwargs = {}

        if self.port is not None:
            args.extend(["--port", "%d" % self.port])
        if self.python_port is not None:
            args.extend(["--python-port", "%d" % self.python_port])
            gateway_kwargs["python_proxy_port"] = self.python_port

        port_used, self.process = launch_gateway(
            self.gateway_class, args
        )
        self.gateway = JavaGateway(gateway_parameters=GatewayParameters(port=port_used), **gateway_kwargs)

    def stop(self):
        # Stop the client gateway
        self.gateway.close()
        # Stop the server process
        self.process.terminate()
        self.process.wait()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def launch_gateway(gateway_class="py4j.GatewayServer", args=[],
                   javaopts=[], redirect_stdout=None, redirect_stderr=None, daemonize_redirect=True):
    """
    Our own more flexble version of Py4J's launch_gateway.
    """
    # Launch the server in a subprocess.
    command = ["java", "-classpath", CLASSPATH] + javaopts + [gateway_class] + args
    proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)

    # Determine which port the server started on (needed to support ephemeral ports)
    # NB: had an odd problem where the server had an error (socket already in use), but didn't exit, so this hangs
    # TODO Look into this at some point
    output = proc.stdout.readline()
    try:
        port_used = int(output)
    except ValueError:
        returncode = proc.poll()
        if returncode is not None:
            raise JavaProcessError("Py4J server process returned with return code %s: %s" % (returncode,
                                                                                             proc.stderr.read()))
        else:
            raise JavaProcessError("invalid output from Py4J server when started: '%s'" % output)

    # Start consumer threads so process does not deadlock/hangs
    OutputConsumer(redirect_stdout, proc.stdout, daemon=daemonize_redirect).start()
    if redirect_stderr is not None:
        OutputConsumer(redirect_stderr, proc.stderr, daemon=daemonize_redirect).start()
    ProcessConsumer(proc, [redirect_stdout], daemon=daemonize_redirect).start()

    return port_used, proc



class DependencyCheckerError(Exception):
    pass


class JavaProcessError(Exception):
    pass
