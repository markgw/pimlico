import os
from collections import deque
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError

import sys
import time

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_DIR
from pimlico.core.logs import get_log_file
from pimlico.core.modules.base import DependencyError
from pimlico.utils.communicate import timeout_process
from py4j.compat import CompatThread, hasattr2, Queue
from py4j.protocol import smart_decode

CLASSPATH = ":".join(["%s/*" % JAVA_LIB_DIR, JAVA_BUILD_DIR])


def call_java(class_name, args=[]):
    # May in future want to allow the path to the java executable to be specified in local config
    process = Popen(["java", "-cp", CLASSPATH, class_name] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    stdout_data, stderr_data = process.communicate()
    return stdout_data, stderr_data, process.returncode


def start_java_process(class_name, args=[], java_args=[], wait=0.1):
    # May in future want to allow the path to the java executable to be specified in local config
    cmd = ["java", "-cp", CLASSPATH] + java_args + [class_name] + args
    process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
    # Attach the command to the Popen object so it's easy to read what was run for debugging
    process.command_run = " ".join(cmd)

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


class Py4JInterface(object):
    def __init__(self, gateway_class, port=None, python_port=None, gateway_args=[], pipeline=None, print_stdout=True,
                 print_stderr=True, env={}, system_properties={}, java_opts=[]):
        """
        If pipeline is given, configuration is looked for there. If found, this overrides config given
        in other kwargs.

        If print_stdout=True (default), stdout from processes will be printed out to the console in addition to any
        other processing that's done to it. Same with stderr.
        By default, both are output to the console.

        env adds extra variables to the environment for running the Java process.

        system_properties adds Java system property settings to the Java command.

        """
        self.java_opts = java_opts
        self.system_properties = system_properties
        self.env = env
        self.print_stderr = print_stderr
        self.print_stdout = print_stdout
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
        self._gateway_kwargs = None
        self._port_used = None
        self.clients = []

    def start(self):
        """
        Start a Py4J gateway server in the background on the given port, which will then be used for
        communicating with the Java app.

        If a port has been given, it is assumed that the gateway accepts a --port option.
        Likewise with python_port and a --python-port option.

        """
        args = list(self.gateway_args)
        self._gateway_kwargs = {}

        if self.port is not None:
            args.extend(["--port", "%d" % self.port])

        if self.python_port is not None:
            args.extend(["--python-port", "%d" % self.python_port])
            self._gateway_kwargs["python_proxy_port"] = self.python_port

        # We could add other things as well here, like queues, to capture the output
        redirect_stdout = []
        if self.print_stdout:
            redirect_stdout.append(sys.stdout)
        redirect_stderr = []
        if self.print_stderr:
            redirect_stderr.append(sys.stderr)

        # Allow Java system properties to be set on the command line
        java_opts = list(self.java_opts)
        for prop, val in self.system_properties.items():
            java_opts.extend(["-D%s=%s" % (prop, val)])

        self._port_used, self.process = launch_gateway(
            self.gateway_class, args,
            redirect_stdout=redirect_stdout, redirect_stderr=redirect_stderr,
            env=self.env, javaopts=java_opts
        )
        self.gateway = self.new_client()

    def new_client(self):
        from py4j.java_gateway import JavaGateway, GatewayParameters
        client = no_retry_gateway(gateway_parameters=GatewayParameters(port=self._port_used), **self._gateway_kwargs)
        self.clients.append(client)
        return client

    def stop(self):
        # Stop the client gateway(s)
        for client_gateway in self.clients:
            client_gateway.close()
        self.gateway = None
        self.clients = []
        # Stop the server process
        try:
            self.process.terminate()
        except OSError, e:
            if e.errno == 3:
                # No such process: process is already dead
                pass
            else:
                # Raise other errors
                raise
        self.process.wait()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def no_retry_gateway(**kwargs):
    """
    A wrapper around the constructor of JavaGateway that produces a version of it that doesn't retry on
    errors. The default gateway keeps retying and outputting millions of errors if the server goes down,
    which makes responding to interrupts horrible (as the server might die before the Python process gets
    the interrupt).

    TODO This isn't working: it just gets worse when I use my version!

    """
    from py4j.java_gateway import JavaGateway, GatewayClient

    class NoRetryGatewayClient(GatewayClient):
        def send_command(self, command, retry=True):
            return super(NoRetryGatewayClient, self).send_command(command, retry=False)

    # Start a JavaGateway as normal
    gateway = JavaGateway(**kwargs)
    # Replace the gateway client
    #gateway_client = NoRetryGatewayClient(
    #    address=gateway._gateway_client.address,
    #    port=gateway._gateway_client.port,
    #    auto_close=gateway._gateway_client.auto_close
    #)
    #gateway.set_gateway_client(gateway_client)
    return gateway


def launch_gateway(gateway_class="py4j.GatewayServer", args=[],
                   javaopts=[], redirect_stdout=None, redirect_stderr=None, daemonize_redirect=True,
                   env={}):
    """
    Our own more flexble version of Py4J's launch_gateway.
    """
    from py4j.java_gateway import ProcessConsumer

    # Add custom environment variables to the ones we've already got
    java_env = os.environ.copy()
    java_env.update(env)

    # Launch the server in a subprocess.
    command = ["java", "-classpath", CLASSPATH] + javaopts + [gateway_class] + args
    proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, env=java_env)

    # Determine which port the server started on (needed to support ephemeral ports)
    # Don't hang on an error running the gateway launcher
    output = None
    try:
        with timeout_process(proc, 10.0):
            output = proc.stdout.readline()
    except Exception, e:
        # Try reading stderr to see if there's any info there
        error_output = proc.stderr.read().strip("\n ")
        err_path = output_p4j_error_info(command, "?", "could not read", error_output)

        raise JavaProcessError("error reading first line from gateway process: %s. Error output: %s (see %s for "
                               "more details)" % (e, error_output, err_path))

    if output is None or proc.poll() == -9:
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

    # Start consumer threads so process does not deadlock/hang
    OutputConsumer(redirect_stdout, proc.stdout, daemon=daemonize_redirect).start()
    if redirect_stderr is not None:
        OutputConsumer(redirect_stderr, proc.stderr, daemon=daemonize_redirect).start()
    ProcessConsumer(proc, [redirect_stdout], daemon=daemonize_redirect).start()

    return port_used, proc


class OutputConsumer(CompatThread):
    """Thread that consumes output
    Modification of Py4J's OutputConsumer to allow multiple redirects.
    """

    def __init__(self, redirects, stream, *args, **kwargs):
        super(OutputConsumer, self).__init__(*args, **kwargs)
        # Also allow the one-redirect case, just like Py4J's class
        if not isinstance(redirects, list):
            redirects = [redirects]
        self.redirects = redirects
        self.stream = stream

        self.redirect_funcs = []
        for redirect in redirects:
            if isinstance(redirect, Queue):
                self.redirect_funcs.append(self._pipe_queue)
            if isinstance(redirect, deque):
                self.redirect_funcs.append(self._pipe_deque)
            if hasattr2(redirect, "write"):
                self.redirect_funcs.append(self._pipe_fd)

    def _pipe_queue(self, redirect, line):
        redirect.put(line)

    def _pipe_deque(self, redirect, line):
        redirect.appendleft(line)

    def _pipe_fd(self, redirect, line):
        redirect.write(line)

    def run(self):
        lines_iterator = iter(self.stream.readline, b"")
        for line in lines_iterator:
            for redirect, fn in zip(self.redirects, self.redirect_funcs):
                fn(redirect, smart_decode(line))


def output_p4j_error_info(command, returncode, stdout, stderr):
    file_path = get_log_file("py4j")
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
