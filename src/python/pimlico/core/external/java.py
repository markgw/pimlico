# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os
from Queue import Empty
from collections import deque
from subprocess import Popen, PIPE, check_output, STDOUT, CalledProcessError

import sys
import time
from cStringIO import StringIO

from pimlico import JAVA_LIB_DIR, JAVA_BUILD_JAR_DIR
from pimlico.core.logs import get_log_file
from pimlico.core.modules.base import DependencyError
from pimlico.utils.communicate import timeout_process
from py4j.compat import CompatThread, hasattr2, Queue
from py4j.protocol import smart_decode, Py4JJavaError

CLASSPATH = ":".join(["%s/*" % JAVA_LIB_DIR, "%s/*" % JAVA_BUILD_JAR_DIR])


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
        raise DependencyCheckerError(
            "could not load Java dependency checker. Have you compiled the Pimlico java core? %s" % (err or ""))

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
                 print_stderr=True, env={}, system_properties={}, java_opts=[], timeout=10., prefix_classpath=None):
        """
        If pipeline is given, configuration is looked for there. If found, this overrides config given
        in other kwargs.

        If print_stdout=True (default), stdout from processes will be printed out to the console in addition to any
        other processing that's done to it. Same with stderr.
        By default, both are output to the console.

        env adds extra variables to the environment for running the Java process.

        system_properties adds Java system property settings to the Java command.

        """
        self.prefix_classpath = prefix_classpath
        self.java_opts = java_opts
        self.system_properties = system_properties
        self.env = env
        self.print_stderr = print_stderr
        self.print_stdout = print_stdout
        self.python_port = python_port
        self.gateway_args = gateway_args
        self.gateway_class = gateway_class
        self.port = port
        self.timeout = timeout

        self.stderr_queue = Queue()
        self.stdout_queue = Queue()

        # Look for config in the pipeline
        if pipeline is not None:
            start_port = pipeline.local_config.get("py4j_port", None)
            if start_port is not None:
                # Config gives just a single port number
                # If it's given, use the following port for the other direction of communication
                self.port = int(start_port)
                self.python_port = int(start_port) + 1
            if "py4j_timeout" in pipeline.local_config:
                # Override the timeout given as an arg
                self.timeout = float(pipeline.local_config["py4j_timeout"])

        self.process = None
        self.gateway = None
        self.port_used = None
        self.clients = []

    def start(self, timeout=None, port_output_prefix=None):
        """
        Start a Py4J gateway server in the background on the given port, which will then be used for
        communicating with the Java app.

        If a port has been given, it is assumed that the gateway accepts a --port option.
        Likewise with python_port and a --python-port option.

        If timeout is given, it overrides any timeout given in the constructor or specified in local config.

        """
        if timeout is None:
            # Use the default timeout specified on the instance
            timeout = self.timeout
        args = list(self.gateway_args)

        if self.port is not None:
            args.extend(["--port", "%d" % self.port])

        if self.python_port is not None:
            args.extend(["--python-port", "%d" % self.python_port])

        # We could add other things as well here, like queues, to capture the output
        redirect_stdout = [self.stdout_queue]
        if self.print_stdout:
            redirect_stdout.append(sys.stdout)
        redirect_stderr = [self.stderr_queue]
        if self.print_stderr:
            redirect_stderr.append(sys.stderr)

        # Allow Java system properties to be set on the command line
        java_opts = list(self.java_opts)
        for prop, val in self.system_properties.items():
            java_opts.extend(["-D%s=%s" % (prop, val)])

        self.port_used, self.process = launch_gateway(
            self.gateway_class, args,
            redirect_stdout=redirect_stdout, redirect_stderr=redirect_stderr,
            env=self.env, javaopts=java_opts,
            startup_timeout=timeout, port_output_prefix=port_output_prefix,
            prefix_classpath=self.prefix_classpath,
        )
        self.gateway = self.new_client()

    def new_client(self):
        client = gateway_client_to_running_server(self.port_used)
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

    def clear_output_queues(self):
        while not self.stdout_queue.empty():
            self.stdout_queue.get_nowait()
        while not self.stderr_queue.empty():
            self.stderr_queue.get_nowait()

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


def gateway_client_to_running_server(port):
    from py4j.java_gateway import GatewayParameters
    return no_retry_gateway(gateway_parameters=GatewayParameters(port=port))


def launch_gateway(gateway_class="py4j.GatewayServer", args=[],
                   javaopts=[], redirect_stdout=None, redirect_stderr=None, daemonize_redirect=True,
                   env={}, port_output_prefix=None, startup_timeout=10., prefix_classpath=None):
    """
    Our own more flexble version of Py4J's launch_gateway.
    """
    from py4j.java_gateway import ProcessConsumer

    # Add custom environment variables to the ones we've already got
    java_env = os.environ.copy()
    java_env.update(env)

    # Allow extra things to be added to the start of the classpath
    if prefix_classpath is not None:
        classpath = ":".join(prefix_classpath.split(":") + CLASSPATH.split(":"))
    else:
        classpath = CLASSPATH

    # Launch the server in a subprocess.
    command = ["java", "-classpath", classpath] + javaopts + [gateway_class] + args
    proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, env=java_env)

    if redirect_stdout is None:
        redirect_stdout = []
    stdout_queue = Queue()

    if redirect_stderr is None:
        redirect_stderr = []
    stderr_capture = StringIO()

    def get_stderr():
        try:
            return stderr_capture.getvalue()
        except Empty:
            return ""

    # Start consumer threads so process does not deadlock/hang
    stdout_consumer = OutputConsumer(redirect_stdout, proc.stdout, daemon=daemonize_redirect,
                                     temporary_redirects=[stdout_queue])
    stderr_consumer = OutputConsumer(redirect_stderr, proc.stderr, daemon=daemonize_redirect,
                                     temporary_redirects=[stderr_capture])
    stdout_consumer.start()
    stderr_consumer.start()
    ProcessConsumer(proc, [redirect_stdout], daemon=daemonize_redirect).start()

    # Determine which port the server started on (needed to support ephemeral ports)
    # Don't hang on an error running the gateway launcher
    output = None
    start_time = time.time()
    remaining_time = time.time() - start_time + startup_timeout
    try:
        while remaining_time > 0.:
            # Get lines from stdout until the timeout is reached
            output = stdout_queue.get(timeout=remaining_time)
            if port_output_prefix is None or output.strip("\n ") == "ERROR":
                # Don't look for a particular prefix, just use the first line we get, or if it's an error
                # don't keep waiting
                break
            elif output.startswith(port_output_prefix):
                # If the line doesn't begin with the right prefix, keep waiting
                # If it does, strip the prefix, so that we get just the port number
                output = output[len(port_output_prefix):]
                break
            remaining_time = time.time() - start_time + startup_timeout
    except Empty:
        # Timed out waiting for server to start
        error_output = get_stderr()
        err_path = output_p4j_error_info(command, "(timed out)", "", error_output)
        try:
            # Give up and kill the process, if it's still running
            proc.terminate()
        except OSError:
            # Already terminated
            pass
        raise JavaProcessError("timed out starting gateway server (for details see %s)" % err_path)
    except Exception, e:
        # Try reading stderr to see if there's any info there
        error_output = get_stderr()
        err_path = output_p4j_error_info(command, "?", "could not read", error_output)

        raise JavaProcessError("error reading first line from gateway process: %s. Error output: %s (see %s for "
                               "more details)" % (e, error_output, err_path))

    # Check whether there was an error reported
    output = output.strip("\n ")
    if output == "ERROR":
        # Read error output from stderr
        error_output = get_stderr()
        raise JavaProcessError("Py4J gateway had an error starting up: %s" % error_output)

    try:
        port_used = int(output)
    except ValueError:
        returncode = proc.poll()

        stderr_output = get_stderr()
        err_path = output_p4j_error_info(command, returncode, output, stderr_output)

        if returncode is not None:
            raise JavaProcessError("Py4J server process returned with return code %s: %s (see %s for details)" %
                                   (returncode, stderr_output, err_path))
        else:
            raise JavaProcessError("invalid first line output from Py4J server when started: '%s' (see %s for details)"
                                   % (output, err_path))

    # Stop the temporary redirects that were only going to capture startup output
    stdout_consumer.remove_temporary_redirects()
    stderr_consumer.remove_temporary_redirects()

    return port_used, proc


def _pipe_queue(redirect, line):
    redirect.put(line)


def _pipe_deque(redirect, line):
    redirect.appendleft(line)


def _pipe_fd(redirect, line):
    redirect.write(line)


def get_redirect_func(redirect):
    if isinstance(redirect, Queue):
        return _pipe_queue
    if isinstance(redirect, deque):
        return _pipe_deque
    if hasattr2(redirect, "write"):
        return _pipe_fd


class OutputConsumer(CompatThread):
    """Thread that consumes output
    Modification of Py4J's OutputConsumer to allow multiple redirects.
    """

    def __init__(self, redirects, stream, *args, **kwargs):
        self.temporary_redirects = kwargs.pop("temporary_redirects", [])
        super(OutputConsumer, self).__init__(*args, **kwargs)
        # Also allow the one-redirect case, just like Py4J's class
        if not isinstance(redirects, list):
            redirects = [redirects]
        self.redirects = redirects
        self.stream = stream

        self.redirect_funcs = [get_redirect_func(redirect) for redirect in self.redirects]
        self.temporary_redirect_funcs = [get_redirect_func(redirect) for redirect in self.temporary_redirects]

    def remove_temporary_redirects(self):
        self.temporary_redirects = []
        self.temporary_redirect_funcs = []

    def run(self):
        lines_iterator = iter(self.stream.readline, b"")
        for line in lines_iterator:
            for redirect, fn in zip(self.redirects, self.redirect_funcs):
                fn(redirect, smart_decode(line))
            for redirect, fn in zip(self.temporary_redirects, self.temporary_redirect_funcs):
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


def make_py4j_errors_safe(fn):
    """
    Decorator for functions/methods that call Py4J. Py4J's exceptions include information that gets retrieved
    from the Py4J server when they're displayed. This is a problem if the server is not longer running and
    raises another exception, making the whole situation very confusing.

    If you wrap your function with this, Py4JJavaErrors will be replaced by our own exception type Py4JSafeJavaError,
    containing some of the information about the Java exception if possible.

    """
    def _wrapped_fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Py4JJavaError, e:
            # Try getting the java exception and string repr, but don't throw everything in the air if we can't
            try:
                java_exception = str(e.java_exception)
            except:
                java_exception = None
            try:
                str_repr = str(e)
            except:
                str_repr = None
            raise Py4JSafeJavaError(java_exception, str_repr)
    return _wrapped_fn


class Py4JSafeJavaError(Exception):
    def __init__(self, java_exception=None, str=None):
        super(Py4JSafeJavaError, self).__init__()
        self.str = str
        self.java_exception = java_exception

    def __str__(self):
        if self.str is not None:
            return self.str
        else:
            return super(Py4JSafeJavaError, self).__str__()


class DependencyCheckerError(Exception):
    pass


class JavaProcessError(Exception):
    pass
