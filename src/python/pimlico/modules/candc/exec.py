import Queue
import multiprocessing
import subprocess

from cStringIO import StringIO

from pimlico.core.external.java import Py4JInterface, OutputConsumer
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, MultiprocessingMapPool, \
    MultiprocessingMapProcess
from pimlico.utils.network import get_unused_local_port


class CandcWorkerProcess(MultiprocessingMapProcess):
    """
    A C&C Soap server, running in the background, and a mechanism to issue parse requests via the Soap client
    to that server.

    """
    def __init__(self, input_queue, output_queue, info, port):
        super(CandcWorkerProcess, self).__init__(input_queue, output_queue, info)

        self.host = "127.0.0.1"
        self.port = port

    def set_up(self):
        # Start up a Soap server in the background
        server_args = [self.info.server_binary, "--models", self.info.model_path,
                       "--server", "%s:%d" % (self.host, self.port)]
        self._server_process = subprocess.Popen(server_args,
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Set off a thread to collect output from stdout and stderr
        self.stdout_queue = Queue.Queue()
        self.stdout_consumer = OutputConsumer(self.stdout_queue, self._server_process.stdout)
        self.stderr_queue = Queue.Queue()
        self.stderr_buffer = StringIO()
        self.stderr_consumer = OutputConsumer([self.stderr_queue, self.stderr_buffer], self._server_process.stderr)

        # The server outputs a line to stderr when it's ready, so we should wait for this before continuing
        try:
            err = self.stderr_queue.get(timeout=10.)
        except Queue.Empty:
            raise CandCServerError("server startup timed out after 10 seconds")

        # Check that the server's running nicely
        if not err.startswith("waiting for connections"):
            raise CandCServerError("server startup failed: %s" % self.stderr_buffer.getvalue())

    def process_document(self, archive, filename, *docs):
        # TODO
        pass

    def tear_down(self):
        self._server_process.terminate()

    @property
    def server_name(self):
        return "c&c/%s:%s" % (self.host, self.port)

    def parse_lines(self, lines):
        # TODO Use as model for parse_document
        """
        Run the Soap client to parse a list of sentences.

        """
        # Put the lines in a temporary file so we can pipe them to the client
        with tempfile.NamedTemporaryFile(delete=True) as input_file:
            # Write the data to the temporary file
            input_file.write("".join("%s\n" % line for line in lines))
            input_file.flush()
            input_file.seek(0)
            # Run the soap client to parse the lines
            raw_output = self._run_client(self._host, self._port, input_file)
        # Parse the output
        return CandCOutput.read_output(raw_output)

    def parse_file(self, filename, split=400):
        # TODO Use as model for parse_document
        """
        Run the Soap client to parse all the sentences in a file.

        If the file is more than C{split} lines long, breaks it into
        multiple files and parses them separately (default 400). This
        helps to avoid buffering problems, so is advisable. Set to 0
        to do no splitting.

        """
        if split:
            # Check file length
            with open(filename, 'r') as input_file:
                lines = len(list(input_file))

            if lines > split:
                raw_outputs = []
                with open(filename, 'r') as input_file:
                    # This file is too long: split it into multiple
                    for part in range(int(math.ceil(float(lines) / split))):
                        with tempfile.NamedTemporaryFile('w') as part_file:
                            # Write this partition of the input into a temp file
                            part_file.writelines(itertools.islice(input_file, split))
                            part_file.seek(0)
                            # Run the parser on this partial file
                            raw_outputs.append(self._run_client(self._host, self._port, part_file))
                            # This is critical! Otherwise the output pipes
                            # get full while parsing long files
                            self.clear_pipes()
                # Combine the output from these parses
                return CandCOutput.read_output("\n\n".join(raw_outputs))

        with open(filename, 'r') as input_file:
            # Run the soap client to parse the lines
            raw_output = self._run_client(self._host, self._port, input_file)
        # Parse the output
        return CandCOutput.read_output(raw_output)

    def _run_client(self, input_data):
        # Run the soap client
        client = subprocess.Popen([self.info.client_binary, "--url", "http://%s:%d" % (self.host, self.port)])
        return client.communicate(input_data)

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
    def start_worker(self):
        return CandcWorkerProcess(self.input_queue, self.output_queue,
                                  self.executor.info, self.executor.interface.port_used)


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        # Start up a single C&C background process
        self.worker_input = multiprocessing.Queue()
        self.worker_output = multiprocessing.Queue()
        self.worker = CandcWorkerProcess(self.worker_input, self.worker_output, self.info, get_unused_local_port())

    def preprocess_parallel(self):
        pass

    def create_pool(self, processes):
        return CandcPool(self, processes)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, doc):
        self.worker.process_document(archive, filename, doc)

    def postprocess(self, error=False):
        self.worker.tear_down()

    def postprocess_parallel(self, error=False):
        pass


class CandCServerError(Exception):
    pass


class CandCOutput(object):
    """
    Simple wrapper around C&C's output string to pull out the different bits.

    """
    def __init__(self, lines):
        self.data = "\n".join(lines)

        ### Parse the parser output
        # Pull out max 1 pos line -- marked by <c>
        pos_lines = [line.partition("<c> ")[2] for line in lines if line.startswith("<c> ")]
        self.pos = pos_lines[0] if len(pos_lines) else None
        # Pull out all dependency lines -- those contained in ()s
        self.dependencies = [line for line in lines if line.startswith("(") and line.endswith(")")]

    def __str__(self):
        dep_lines = "\n".join(self.dependencies)
        pos_line = "\n<c> %s" % self.pos if self.pos else ""
        return "%s%s" % (dep_lines, pos_line)

    @staticmethod
    def read_output(data):
        # Split up the data on blank lines
        outputs_lines = [o.split("\n") for o in data.split("\n\n")]
        # Ignore blank lines and comment lines
        outputs_lines = [[line for line in lines if line and not line.startswith("#")]
                         for lines in outputs_lines]
        outputs_lines = [ls for ls in outputs_lines if len(ls)]
        # Parse each as an individual parser output
        return [CandCOutput(output) for output in outputs_lines]
