from py4j.java_collections import ListConverter

from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor, skip_invalid


class ModuleExecutor(DocumentMapModuleExecutor):
    def preprocess(self):
        # Start a tokenizer process
        self.coref = StreamResolver(self.info.model_path, pipeline=self.info.pipeline)
        try:
            self.coref.start()
        except JavaProcessError, e:
            raise ModuleExecutionError("error starting coref process: %s" % e)

        # Don't parse the parse trees, since OpenNLP does that for us, straight from the text
        self.input_corpora[0].raw_data = True

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Input is a list of parse trees: split them up (into sentences)
        tree_strings = doc.split("\n\n")
        # Run coref
        coref_output = self.coref.coref_resolve(tree_strings)
        # TODO Work out what to output
        return coref_output

    def postprocess(self, error=False):
        self.coref.stop()
        self.coref = None


class StreamResolver(object):
    def __init__(self, model_path, pipeline=None):
        self.pipeline = pipeline
        self.model_path = model_path
        self.interface = None

    def coref_resolve(self, sentences):
        # Use OpenNLP's tool to read the PTB trees into Parse data structures
        parse_list = [
            # TODO This isn't working yet
            self.interface.gateway.opennlp.tools.parser.Parse.parseParse(tree)
            for tree in sentences
        ]
        # Convert Python list to Java list
        parse_list = ListConverter().convert(parse_list, self.interface.gateway._gateway_client)
        # Resolve coreference
        return list(self.interface.gateway.entry_point.resolveCoreference(parse_list))

    def start(self):
        # Start a tokenizer process running in the background via Py4J
        self.interface = Py4JInterface("pimlico.opennlp.CoreferenceResolverGateway", gateway_args=[self.model_path],
                                       pipeline=self.pipeline)
        self.interface.start()

    def stop(self):
        self.interface.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
