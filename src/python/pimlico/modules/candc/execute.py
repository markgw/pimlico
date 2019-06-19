# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from __future__ import absolute_import
from __future__ import print_function

import Queue
import multiprocessing
import subprocess
from Queue import Empty
from subprocess import PIPE

from cStringIO import StringIO

from pimlico.core.external.java import OutputConsumer
from pimlico.core.logs import get_log_file
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import MultiprocessingMapProcess, multiprocessing_executor_factory
from pimlico.old_datatypes.base import InvalidDocument
from pimlico.old_datatypes.parse.candc import CandcOutput
from pimlico.utils.network import get_unused_local_ports


class CandcWorkerProcess(MultiprocessingMapProcess):
    """
    A C&C Soap server, running in the background, and a mechanism to issue parse requests via the Soap client
    to that server.

    """
    def __init__(self, input_queue, output_queue, exception_queue, executor):
        self._server_process = None
        self.host = "127.0.0.1"
        # Get one of the ports that the executor lined up for us
        try:
            self.port = executor.ports.get_nowait()
        except Empty:
            raise CandCServerError("not enough ports for all the processes")
        super(CandcWorkerProcess, self).__init__(input_queue, output_queue, exception_queue, executor)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, *docs):
        # Encode doc as utf-8 so it can be sent to the server
        doc = docs[0].encode("utf-8")
        stdout, stderr, returncode = self._run_client(doc)
        self.clear_pipes()
        if returncode != 0:
            # Client call had a non-zero return code -- some kind of error
            return InvalidDocument(
                self.info.module_name,
                "Non-zero return code from SOAP client: %s\n\nStdout:\n%s\n\nStderr:\n%s" %
                (returncode, stdout, stderr)
            )
        else:
            return CandcOutput(stdout.decode("utf-8"))

    def _run_client(self, input_data):
        # Run the soap client
        client_command = [self.info.client_binary, "--url", "http://%s:%d" % (self.host, self.port)]
        client = subprocess.Popen(client_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = client.communicate(input_data)
        return stdout, stderr, client.returncode

    def set_up(worker):
        # Start up a Soap server in the background
        server_args = [worker.info.server_binary, "--models", worker.info.model_path,
                       "--server", "%s:%d" % (worker.host, worker.port)]
        worker._server_process = subprocess.Popen(server_args,
                                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Set off a thread to collect output from stdout and stderr
        worker.stdout_queue = Queue.Queue()
        worker.stdout_buffer = StringIO()
        worker.stdout_consumer = OutputConsumer([worker.stdout_queue, worker.stdout_buffer], worker._server_process.stdout)
        worker.stdout_consumer.start()
        worker.stderr_queue = Queue.Queue()
        worker.stderr_buffer = StringIO()
        worker.stderr_consumer = OutputConsumer([worker.stderr_queue, worker.stderr_buffer], worker._server_process.stderr)
        worker.stderr_consumer.start()

        # Allow the local config to override the default startup timeout
        local_conf = worker.info.pipeline.local_config
        timeout = float(local_conf.get("candc_timeout", 10.))

        # The server outputs a line to stderr when it's ready, so we should wait for this before continuing
        try:
            err = worker.stderr_queue.get(timeout=timeout)
        except Queue.Empty:
            err_path = output_candc_error_info(server_args, worker._server_process.returncode,
                                               worker.stdout_buffer.getvalue(), worker.stderr_buffer.getvalue())
            raise CandCServerError("server startup timed out after %.0f seconds. See %s for more details" %
                                   (timeout, err_path))

        # Check that the server's running nicely
        if not err.startswith("waiting for connections"):
            err_path = output_candc_error_info(server_args, worker._server_process.returncode,
                                               worker.stdout_buffer.getvalue(), worker.stderr_buffer.getvalue())
            raise CandCServerError("server startup failed: %s. See %s for more details" %
                                   (worker.stderr_buffer.getvalue(), err_path))

    def tear_down(self):
        if self._server_process is not None:
            self._server_process.terminate()

    def clear_pipes(self):
        """
        Flush any process output out of the stderr and stdout pipes. This should be done when you know
        you won't want the output again, e.g. once a parse job has completed successfully.

        """
        while not self.stderr_queue.empty():
            self.stderr_queue.get_nowait()
        while not self.stdout_queue.empty():
            self.stdout_queue.get_nowait()

    def alive(self):
        return self._server_process.poll() is None


def preprocess(executor):
    executor.input_corpora[0].raw_data = True
    # Generate enough ports for all the processes
    executor.ports = multiprocessing.Queue()
    for port in get_unused_local_ports(executor.processes):
        executor.ports.put(port)


ModuleExecutor = multiprocessing_executor_factory(
    CandcWorkerProcess, preprocess_fn=preprocess
)


class CandCServerError(Exception):
    pass


def output_candc_error_info(command, returncode, stdout, stderr):
    file_path = get_log_file("candc")
    with open(file_path, "w") as f:
        print("Command:", file=f)
        print(" ".join(command), file=f)
        print("Return code: %s" % returncode, file=f)
        print("Read from stdout:", file=f)
        print(stdout, file=f)
        print("Read from stderr:", file=f)
        print(stderr, file=f)
    return file_path
