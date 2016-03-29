import os
import time
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_DIR, PIMLICO_ROOT

from pimlico.core.modules.base import DependencyError
from pimlico.utils.communicate import timeout_process


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
    def __init__(self, gateway_class, port=None, python_port=None, gateway_args=[], pipeline=None):
        """
        If pipeline is given, configuration is looked for there. If found, this overrides config given
        in other kwargs.

        """
        self.python_port = python_port
        self.gateway_args = gateway_args
        self.gateway_class = gateway_class
        self.port = port

        # Look for config in the pipeline
        start_port = pipeline.local_config.get("py4j_port", None)
        if start_port is not None:
            # Config gives just a single port number
            # If it's given, use the following port for the other direction of communication
            self.port = int(start_port)
            self.python_port = int(start_port) + 1

        self.process = None
        self.gateway = None

    def start(self):
        """
        Start a Py4J gateway server in the background on the given port, which will then be used for
        communicating with the Java app.

        If a port has been given, it is assumed that the gateway accepts a --port option.
        Likewise with python_port and a --python-port option.

        """
        from py4j.java_gateway import JavaGateway, GatewayParameters

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
    from py4j.java_gateway import OutputConsumer, ProcessConsumer

    # Launch the server in a subprocess.
    command = ["java", "-classpath", CLASSPATH] + javaopts + [gateway_class] + args
    proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)

    # Determine which port the server started on (needed to support ephemeral ports)
    # Don't hang on an error running the gateway launcher
    output = None
    try:
        with timeout_process(proc, 3.0):
            output = proc.stdout.readline()
    except Exception, e:
        # Try reading stderr to see if there's any info there
        error_output = proc.stderr.read().strip("\n ")
        err_path = output_p4j_error_info(command, "?", "could not read", error_output)

        raise JavaProcessError("error reading first line from gateway process: %s. Error output: %s (see %s for "
                               "more details)" % (e, error_output, err_path))

    if output is None:
        error_output = proc.stderr.read().strip("\n ")
        err_path = output_p4j_error_info(command, "(timed out)", "", error_output)
        raise JavaProcessError("timed out starting gateway server (for details see %s)" % err_path)

    # Check whether there was an error reported
    output = output.strip("\n ")
    if output == "ERROR":
        # Read error output from stderr
        error_output = proc.stderr.read().strip("\n ")
        raise JavaProcessError("Py4J gateway had an error starting up: %s" % error_output)

    try:
        port_used = int(output)
    except ValueError:
        returncode = proc.poll()

        stderr_output = proc.stderr.read().strip("\n ")
        err_path = output_p4j_error_info(command, returncode, output, stderr_output)

        if returncode is not None:
            raise JavaProcessError("Py4J server process returned with return code %s: %s (see %s for details)" %
                                   (returncode, stderr_output, err_path))
        else:
            raise JavaProcessError("invalid output from Py4J server when started: '%s' (see %s for details)" %
                                   (output, err_path))

    # Start consumer threads so process does not deadlock/hangs
    OutputConsumer(redirect_stdout, proc.stdout, daemon=daemonize_redirect).start()
    if redirect_stderr is not None:
        OutputConsumer(redirect_stderr, proc.stderr, daemon=daemonize_redirect).start()
    ProcessConsumer(proc, [redirect_stdout], daemon=daemonize_redirect).start()

    return port_used, proc


def output_p4j_error_info(command, returncode, stdout, stderr):
    file_path = os.path.abspath(os.path.join(PIMLICO_ROOT, "py4j.err"))
    with open(file_path, "w") as f:
        print >>f, "Command:"
        print >>f, " ".join(command)
        print >>f, "Return code: %s" % returncode
        print >>f, "Read from stdout:"
        print >>f, stdout
        print >>f, "Read from stderr:"
        print >>f, stderr
    return file_path


class DependencyCheckerError(Exception):
    pass


class JavaProcessError(Exception):
    pass
