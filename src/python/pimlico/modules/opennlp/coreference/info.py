"""
.. todo::

   Document this module

"""
import os

from pimlico import MODEL_DIR
from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.coref.opennlp import CorefCorpus, CorefCorpusWriter
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus


WORDNET_DIR = os.path.join(MODEL_DIR, "wordnet", "db-3.1")


class ModuleInfo(DocumentMapModuleInfo):
    """
    Use local config setting opennlp_memory to set the limit on Java heap memory for the OpenNLP processes. If
    parallelizing, this limit is shared between the processes. That is, each OpenNLP worker will have a memory
    limit of `opennlp_memory / processes`. That setting can use `g|G|m|M|k|K`, as in the Java setting.

    """
    module_type_name = "opennlp_coref"
    module_readable_name = "OpenNLP coreference resolution"
    module_inputs = [("parses", ConstituencyParseTreeCorpus)]
    module_outputs = [("coref", CorefCorpus)]
    module_options = {
        "model": {
            "help": "Coreference resolution model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in "
                    "models/opennlp/)",
            "default": "",
        },
        "gzip": {
            "help": "If True, each output, except annotations, for each document is gzipped. This can help reduce the "
                    "storage occupied by e.g. parser or coref output. Default: False",
            "type": str_to_bool,
        },
        "readable": {
            "help": "If True, pretty-print the JSON output, so it's human-readable. Default: False",
            "type": str_to_bool,
        },
        "timeout": {
            "help": "Timeout in seconds for each individual coref resolution task. If this is exceeded, an "
                    "InvalidDocument is returned for that document",
            "type": int,
        }
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "opennlp")

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # We need Py4j to call the tokenizer
        try:
            import py4j
        except ImportError:
            missing_dependencies.append(("Py4J", self.module_name, "Install in lib/python/ dir using 'make py4j'"))

        # Check whether the OpenNLP POS tagger is available
        try:
            class_name = "pimlico.opennlp.CoreferenceResolverGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP coref wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the OpenNLP Java wrapper module provided with "
                                             "Pimlico" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        # Check model files are available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(("OpenNLP coref model", self.module_name,
                                         "Path %s does not exist" % self.model_path))

        # For coref, we also need WordNet dictionary files
        if not os.path.exists(WORDNET_DIR):
            missing_dependencies.append(("WordNet dictionaries", self.module_name,
                                         "Download together with OpenNLP coref model using 'make opennlp' in model dir"
                                         ))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, output_dir, append=False):
        return CorefCorpusWriter(
            output_dir,
            gzip=self.options["gzip"],
            readable=self.options["readable"],
            append=append
        )

    def get_heap_memory_limit(self):
        """
        Read in the local config setting opennlp_memory to compute the memory limit per process for Java
        processes.

        """
        # Read in the local config setting
        limit_string = self.pipeline.local_config.get("opennlp_memory", "5G").upper()
        # Get the limit in bytes
        if limit_string.endswith("K"):
            limit = int(limit_string[:-1]) * 1e3
        elif limit_string.endswith("M"):
            limit = int(limit_string[:-1]) * 1e6
        elif limit_string.endswith("G"):
            limit = int(limit_string[:-1]) * 1e9
        else:
            limit = int(limit_string)
        # Divide the allowed memory between the processes
        process_limit = limit / self.pipeline.processes
        # Convert back to a string for the Java option
        # Use units, so debugging output is clearer if we ever need to output the java command
        if process_limit >= 1e10:
            # If the memory per process is over 10G, we can happily round to the nearest G
            process_limit_string = "%dG" % int(process_limit / 1e9)
        elif process_limit >= 1e7:
            process_limit_string = "%dM" % int(process_limit / 1e6)
        elif process_limit >= 1e4:
            process_limit_string = "%dK" % int(process_limit / 1e3)
        else:
            # Just put the whole number
            process_limit_string = "%d" % process_limit
        return process_limit_string
