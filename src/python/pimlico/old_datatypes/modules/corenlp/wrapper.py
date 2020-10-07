# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Wrapper around Stanford CoreNLP to call it via its server interface.

NB: This module imports some of the Stanford modules' dependencies. Don't import it from ModuleInfo modules.

Client-side code based on Smitha Milli's CoreNLP client: https://github.com/smilli/py-corenlp.

"""
from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
import json
import os
import threading
import warnings

import requests
import time

from pimlico.core.external.java import start_java_process
from pimlico.core.logs import get_log_file
from pimlico.core.modules.execute import StopProcessing
from pimlico.old_datatypes.modules.corenlp import CoreNLPClientError, CoreNLPProcessingError
from pimlico.utils.communicate import timeout_process
from pimlico.utils.pipes import OutputQueue


class CoreNLP(object):
    def __init__(self, pipeline, timeout=None, classpath=None):
        self.classpath = classpath
        self.timeout = timeout
        self.port = int(pipeline.local_config.get("corenlp_port", 9000))
        self.proc = None

        self.server_url = "http://localhost:%d" % self.port
        self._server_cmd = None
        self._shutdown_key = None

        # Flag tells us whether the server has been deliberately killed
        # When a client (which might be in a thread) finds the server's disappeared, it can respond in the knowledge
        #  that the server was killed by another thread (e.g. main) and didn't just have an error
        self.server_killed = threading.Event()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def start(self):
        # Start server
        args = ["-port", "%d" % self.port]
        if self.timeout is not None:
            # Override the server's default timeout
            args.extend(["-timeout", "%d" % int(self.timeout*1000)])
        # Wait a moment and check that it's started up
        self.proc = start_java_process("edu.stanford.nlp.pipeline.StanfordCoreNLPServer",
                                       args=args,
                                       java_args=["-mx4g"], wait=0.4, classpath=self.classpath)
        # Put queues around the outputs, so we can read without blocking
        self.stdout_queue = OutputQueue(self.proc.stdout)
        self.stderr_queue = OutputQueue(self.proc.stderr)
        # Check that the server's responding
        # If it responds straight away, great; otherwise retry a few times
        for i in range(10):
            try:
                self.ping()
            except CoreNLPClientError:
                time.sleep(0.1)
            else:
                break
        # Read shutdown key straight away, as the temporary file where it was written might not exist when we need it
        shutdown_key_filename = "/tmp/corenlp.shutdown"
        if not os.path.exists(shutdown_key_filename):
            warnings.warn("CoreNLP server started up ok, but hasn't output its shutdown key to a file, so we won't be "
                          "able to shut it down gracefully")
        else:
            with open(shutdown_key_filename, "r") as f:
                self._shutdown_key = f.read()

    def send_shutdown(self):
        """
        Sends the stop signal to the server. Doesn't wait for it to stop.
        """
        # Set our own flag so everyone knows that if the server disappears it's because we killed it
        self.server_killed.set()
        # If we were able to read the shutdown key when we started the server, we can tell it to shut down
        if self._shutdown_key is not None:
            requests.get("%s/shutdown" % self.server_url, {"key": self._shutdown_key})

    def shutdown(self):
        try:
            self.ping()
        except CoreNLPClientError:
            # Server's not running -- no need to shut down
            return

        if self._shutdown_key is None:
            # We have no shutdown key, so we can't shut down nicely
            # Just kill the process
            self.server_killed.set()
            self.proc.kill()
            return

        try:
            # Send stop signal to server
            self.send_shutdown()
        except requests.exceptions.ConnectionError:
            # Server's clearly already gone down -- fine
            return
        # Wait for it to shutdown
        # Give up after 3 secs
        shutdown = False
        with timeout_process(self.proc, 3.0):
            self.proc.wait()
            shutdown = True
        if not shutdown:
            warnings.warn("Had to kill CoreNLP server, as it was taking too long to shut down")

    def annotate(self, text, properties=None):
        if not text.strip():
            # No input text: don't pass into the CoreNLP server, as it gets thrown off by this
            return {"sentences": []}

        if properties is None:
            params = {}
        else:
            params = {"properties": str(properties)}

        try:
            r = requests.get(self.server_url, params=params, data=text)
        except requests.exceptions.ConnectionError as e:
            if self.server_killed.is_set():
                # Raise a special exception, since we know the server was taken down deliberately
                raise StopProcessing("CoreNLP server was killed")
            else:
                raise CoreNLPClientError("Did not get a response from CoreNLP server at %s. Server must be started "
                                         "before calling annotate()" % self.server_url)

        if r.status_code != 200:
            # Not a happy server
            err_path = self.output_corenlp_error_info(text, r.status_code, r.text)
            raise CoreNLPProcessingError("error in CoreNLP processing: %s. For more details, see %s" %
                                         (". ".join(r.text.strip("\n ").splitlines()), err_path))

        try:
            output = json.loads(r.text, strict=False)
        except Exception as e:
            err_path = self.output_corenlp_error_info(text, r.status_code, r.text)
            raise CoreNLPClientError("Could not parse JSON response from the CoreNLP server: %s. For more details, "
                                     "see %s" % (e, err_path))

        # Don't need the output from stdout/err, but clear the pipes anyway
        # Important: if we don't do this, they fill up and things grind to a halt
        self.read_server_stderr(), self.read_server_stdout()
        return output

    def tokensregex(self, text, pattern, filter):
        return self.regex("/tokensregex", text, pattern, filter)

    def semgrex(self, text, pattern, filter):
        return self.regex("/semgrex", text, pattern, filter)

    def regex(self, endpoint, text, pattern, filter):
        r = requests.get(
            self.server_url + endpoint,
            params={
                "pattern":  pattern,
                "filter": filter
            },
            data=text
        )
        try:
            output = json.loads(r.text)
        except Exception as e:
            raise CoreNLPClientError("Could not parse JSON response from the CoreNLP server: %s" % e)
        return output

    def ping(self):
        try:
            r = requests.get("%s/ping" % self.server_url)
        except requests.exceptions.ConnectionError as e:
            raise CoreNLPClientError("couldn't reach server for ping: %s" % e)
        if r.text.strip("\n ") != "pong":
            raise CoreNLPClientError("server ping got non-pong response: %s" % r.text)

    def read_server_stderr(self):
        return self.stderr_queue.get_available()

    def read_server_stdout(self):
        return self.stdout_queue.get_available()

    def output_corenlp_error_info(self, input_text, status_code, response):
        stdout, stderr = self.read_server_stdout(), self.read_server_stderr()

        file_path = get_log_file("corenlp")
        with open(file_path, "w") as f:
            print("## Response status code: %s" % status_code, file=f)
            print("## Server response:\n%s" % response, file=f)
            print("## Read from stdout:", file=f)
            print(stdout, file=f)
            print("## Read from stderr:", file=f)
            print(stderr, file=f)
            print("## Server command:", file=f)
            print(self.proc.command_run, file=f)
            print("## Server URL:", file=f)
            print(self.server_url, file=f)
            print("## Input:", file=f)
            print(input_text, file=f)
        return file_path
