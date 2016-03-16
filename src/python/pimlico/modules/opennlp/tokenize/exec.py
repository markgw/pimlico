from pimlico.core.external.java import start_java_process
from pimlico.core.modules.map import DocumentMapModuleExecutor
from pimlico.utils.communicate import StreamCommunicationPacket


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self, info):
        # Start a tokenizer process
        self.tokenizer = StreamTokenizer(info.sentence_model_path, info.token_model_path)
        self.tokenizer.start()

    def process_document(self, filename, doc):
        # Run tokenization
        return self.tokenizer.tokenize(doc)

    def postprocess(self, info):
        self.tokenizer.stop()
        self.tokenizer = None


class StreamTokenizer(object):
    def __init__(self, sentence_model_path, token_model_path):
        self.token_model_path = token_model_path
        self.sentence_model_path = sentence_model_path

        self.process = None

    def tokenize(self, document):
        packet = StreamCommunicationPacket(document)
        # Send this to the Java process
        self.process.stdin.write(packet.encode())
        # Receive the response, blocking until it's ready
        return StreamCommunicationPacket.read(self.process.stdout)

    def start(self):
        # Start a tokenizer process running in the background
        self.process = start_java_process("pimlico.opennlp.Tokenize",
                                          [self.sentence_model_path, self.token_model_path])

    def stop(self):
        # Close stdin, which should issue an EOF to the Java input stream
        self.process.stdin.close()
        # Wait until the process terminates
        self.process.wait()

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
