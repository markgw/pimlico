import Queue
import subprocess
from cStringIO import StringIO
from subprocess import PIPE

from pimlico.core.external.java import OutputConsumer
from pimlico.core.logs import get_log_file
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, MultiprocessingMapPool, \
    MultiprocessingMapProcess
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.parse.candc import CandcOutput
from pimlico.utils.network import get_unused_local_ports


class CandcWorkerProcess(MultiprocessingMapProcess):
    """
    A C&C Soap server, running in the background, and a mechanism to issue parse requests via the Soap client
    to that server.

    """
    def __init__(self, input_queue, output_queue, info, port):
        self._server_process = None
        self.host = "127.0.0.1"
        self.port = port
        super(CandcWorkerProcess, self).__init__(input_queue, output_queue, info)

    def set_up(self):
        # Start up a Soap server in the background
        server_args = [self.info.server_binary, "--models", self.info.model_path,
                       "--server", "%s:%d" % (self.host, self.port)]
        self._server_process = subprocess.Popen(server_args,
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Set off a thread to collect output from stdout and stderr
        self.stdout_queue = Queue.Queue()
        self.stdout_buffer = StringIO()
        self.stdout_consumer = OutputConsumer([self.stdout_queue, self.stdout_buffer], self._server_process.stdout)
        self.stdout_consumer.start()
        self.stderr_queue = Queue.Queue()
        self.stderr_buffer = StringIO()
        self.stderr_consumer = OutputConsumer([self.stderr_queue, self.stderr_buffer], self._server_process.stderr)
        self.stderr_consumer.start()

        # The server outputs a line to stderr when it's ready, so we should wait for this before continuing
        try:
            err = self.stderr_queue.get(timeout=10.)
        except Queue.Empty:
            err_path = output_candc_error_info(server_args, self._server_process.returncode,
                                               self.stdout_buffer.getvalue(), self.stderr_buffer.getvalue())
            raise CandCServerError("server startup timed out after 10 seconds. See %s for more details" % err_path)

        # Check that the server's running nicely
        if not err.startswith("waiting for connections"):
            err_path = output_candc_error_info(server_args, self._server_process.returncode,
                                               self.stdout_buffer.getvalue(), self.stderr_buffer.getvalue())
            raise CandCServerError("server startup failed: %s. See %s for more details" %
                                   (self.stderr_buffer.getvalue(), err_path))

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, *docs):
        # TODO Maybe split up into multiple requests if there's a problem with large docs
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

    def tear_down(self):
        if self._server_process is not None:
            self._server_process.terminate()

    def _run_client(self, input_data):
        # Run the soap client
        client_command = [self.info.client_binary, "--url", "http://%s:%d" % (self.host, self.port)]
        client = subprocess.Popen(client_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = client.communicate(input_data)
        return stdout, stderr, client.returncode

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


class CandcPool(MultiprocessingMapPool):
    """
    Simple pool for sending off multiple calls to the Py4J gateway at once.

    """

    def __init__(self, executor, processes):
        # Generate enough ports for all the processes
        self._ports = iter(get_unused_local_ports(processes))
        super(CandcPool, self).__init__(executor, processes)

    def start_worker(self):
        return CandcWorkerProcess(self.input_queue, self.output_queue, self.executor.info, self._ports.next())


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        # Start up a single C&C background process
        self.log.info("Starting single C&C background process")
        self.single_pool = CandcPool(self, 1)
        self.log.info("C&C process initialized")

        self.input_corpora[0].raw_data = True

    def preprocess_parallel(self):
        self.input_corpora[0].raw_data = True

    def create_pool(self, processes):
        return CandcPool(self, processes)

    def process_document(self, archive, filename, *docs):
        self.single_pool.input_queue.put((archive, filename, docs))
        # Wait for output
        return self.single_pool.output_queue.get().data

    def postprocess(self, error=False):
        self.single_pool.shutdown()

    def postprocess_parallel(self, error=False):
        pass


class CandCServerError(Exception):
    pass


def output_candc_error_info(command, returncode, stdout, stderr):
    file_path = get_log_file("candc")
    with open(file_path, "w") as f:
        print >>f, "Command:"
        print >>f, " ".join(command)
        print >>f, "Return code: %s" % returncode
        print >>f, "Read from stdout:"
        print >>f, stdout
        print >>f, "Read from stderr:"
        print >>f, stderr
    return file_path
