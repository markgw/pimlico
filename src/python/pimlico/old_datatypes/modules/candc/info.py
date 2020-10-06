# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Wrapper around the original `C&C parser <http://svn.ask.it.usyd.edu.au/trac/candc/>`_.

Takes tokenized input and parses it with C&C. The output is written exactly as it comes out from C&C.
It contains both GRs and supertags, plus POS-tags, etc.

The wrapper uses C&C's SOAP server. It sets the SOAP server running in the background and then calls C&C's
SOAP client for each document. If parallelizing, multiple SOAP servers are set going and each one is kept
constantly fed with documents.

.. todo::

   Update to new datatypes system and add test pipeline

"""
import os

from pimlico import LIB_DIR
from pimlico.core.dependencies.base import SoftwareDependency
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.old_datatypes.parse.candc import CandcOutputCorpusWriter, CandcOutputCorpus
from pimlico.old_datatypes.tar import TarredCorpusType
from pimlico.old_datatypes.tokenized import TokenizedDocumentType


CANDC_BINARY_DIR = os.path.join(LIB_DIR, "bin", "candc")


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "candc"
    module_readable_name = "C&C parser"
    module_inputs = [("documents", TarredCorpusType(TokenizedDocumentType))]
    module_outputs = [("parsed", CandcOutputCorpus)]
    module_options = {
        "model": {
            "help": "Absolute path to models directory or name of model set. If not an absolute path, assumed to be "
                    "a subdirectory of the candcs models dir (see instructions in models/candc/README on how to fetch "
                    "pre-trained models)",
            "default": "ccgbank",
        },
    }
    module_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "candc")
        self.server_binary = os.path.join(CANDC_BINARY_DIR, "soap_server")
        self.client_binary = os.path.join(CANDC_BINARY_DIR, "soap_client")

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Make sure the model files are available
        if not os.path.exists(self.model_path):
            problems.append(
                ("missing C&C model", "Parsing model directory doesn't exist: %s. Download a suitable pre-trained "
                                      "model, or make sure you've specified the model name corectly" % self.model_path)
            )
        return problems

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [CandcParserDependency()]

    def get_writer(self, output_name, output_dir, append=False):
        return CandcOutputCorpusWriter(output_dir, append=append)


class CandcParserDependency(SoftwareDependency):
    """
    The C&C parser cannot be installed automatically, since it requires a login to download it. Instead,
    we provide instructions for downloading and building it.

    """
    def __init__(self):
        super(CandcParserDependency, self).__init__("candc", homepage_url="https://github.com/chrzyki/candc")

    def problems(self, local_config):
        binaries = [os.path.join(CANDC_BINARY_DIR, binary) for binary in ["soap_server", "soap_client"]]
        return super(CandcParserDependency, self).problems(local_config) + [
            "missing binary %s" % binary for binary in binaries if not os.path.exists(binary)
        ]

    def installable(self):
        return False

    def installation_instructions(self):
        return "C&C parser binary must be built in %s. We cannot do this automatically, since you need to sign up " \
               "for an account on the website and download the parser. See %s/bin/README_CANDC for instructions on " \
               "fetching and building it" % (CANDC_BINARY_DIR, LIB_DIR)
