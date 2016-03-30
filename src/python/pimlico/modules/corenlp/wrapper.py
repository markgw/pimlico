"""
Wrapper around Stanford CoreNLP to call it via its server interface.

NB: This module imports some of the Stanford modules' dependencies. Don't import it from ModuleInfo modules.

Client-side code based on Smitha Milli's CoreNLP client: https://github.com/smilli/py-corenlp.

"""
import json
import warnings

import requests
from pimlico.core.external.java import start_java_process
from pimlico.core.logs import get_log_file
from pimlico.modules.corenlp import CoreNLPClientError, CoreNLPProcessingError
from pimlico.utils.communicate import timeout_process
from pimlico.utils.pipes import OutputQueue


class CoreNLP(object):
    def __init__(self, pipeline):
        self.port = int(pipeline.local_config.get("corenlp_port", 9000))
        self.proc = None

        self.server_url = "http://localhost:%d" % self.port
        self._server_cmd = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def start(self):
        # Start server
        # Wait a moment and check that it's started up
        self.proc = start_java_process("edu.stanford.nlp.pipeline.StanfordCoreNLPServer",
                                       args=["-port", "%d" % self.port],
                                       java_args=["-mx4g"], wait=0.4)
        # Put queues around the outputs, so we can read without blocking
        self.stdout_queue = OutputQueue(self.proc.stdout)
        self.stderr_queue = OutputQueue(self.proc.stderr)
        # Check that the server's responding
        self.ping()

    def send_shutdown(self):
        """
        Sends the stop signal to the server. Doesn't wait for it to stop.
        """
        # Read the shutdown key that should have been stored when the server started
        with open("/tmp/corenlp.shutdown", "r") as f:
            shutdown_key = f.read()
        requests.get("%s/shutdown" % self.server_url, {"key": shutdown_key})

    def shutdown(self):
        try:
            self.ping()
        except CoreNLPClientError:
            # Server's not running -- no need to shut down
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
            r = requests.get(self.server_url, params=params, data=text, timeout=10.)
        except requests.exceptions.ConnectionError:
            raise CoreNLPClientError("Did not get a response from CoreNLP server at %s. Server must be started "
                                     "before calling annotate()" % self.server_url)

        if r.status_code != 200:
            # Not a happy server
            err_path = self.output_corenlp_error_info(text, r.status_code, r.text)
            raise CoreNLPProcessingError("error in CoreNLP processing: %s. For more details, see %s" %
                                         (". ".join(r.text.strip("\n ").splitlines()), err_path))

        try:
            output = json.loads(r.text, strict=False)
        except Exception, e:
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
        except Exception, e:
            raise CoreNLPClientError("Could not parse JSON response from the CoreNLP server: %s" % e)
        return output

    def ping(self):
        try:
            r = requests.get("%s/ping" % self.server_url)
        except requests.exceptions.ConnectionError, e:
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
            print >>f, "## Response status code: %s" % status_code
            print >>f, "## Server response:\n%s" % response
            print >>f, "## Read from stdout:"
            print >>f, stdout
            print >>f, "## Read from stderr:"
            print >>f, stderr
            print >>f, "## Server command:"
            print >>f, self.proc.command_run
            print >>f, "## Server URL:"
            print >>f, self.server_url
            print >>f, "## Input:"
            print >>f, input_text
        return file_path
