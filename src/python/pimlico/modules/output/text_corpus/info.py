# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Output module for producing a directory containing a text corpus, with
documents stored in separate files.

The input must be a raw text grouped corpus. Corpora with other document
types can be converted to raw text using the :mod:`~pimlico.modules.corpora.format`
module.

"""
from pimlico.core.dependencies.licenses import PSF

from pimlico.core.dependencies.python import PythonPackageOnPip
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool, choose_from_list
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "text_corpus"
    module_readable_name = "Text corpus directory"
    module_inputs = [
        ("corpus", GroupedCorpus(RawTextDocumentType())),
    ]
    module_options = {
        "path": {
            "help": "Directory to write the corpus to",
            "required": True,
        },
        "archive_dirs": {
            "help": "Create a subdirectory for each archive of the grouped corpus to store that archive's "
                    "documents in. Otherwise, all documents are stored in the same directory (or subdirectories "
                    "where the document names include directory separators)",
            "type": str_to_bool,
        },
        "suffix": {
            "help": "Suffix to use for each document's filename",
        },
        "invalid": {
            "help": "What to do with invalid documents (where there's been a problem reading/processing the document "
                    "somewhere in the pipeline). 'skip' (default): don't output the document at all. 'empty': "
                    "output an empty file",
            "type": choose_from_list(["skip", "empty"]),
            "default": "skip",
        },
        "tar": {
            "help": "Add all files to a single tar archive, instead of just outputting to disk in the given "
                    "directory. This is a good choice for very large corpora, for which storing to files on "
                    "disk can cause filesystem problems. If given, the value is used as the basename for "
                    "the tar archive. Default: do not output tar",
        },
    }
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            PythonPackageOnPip("contextlib2", homepage_url="https://contextlib2.readthedocs.io/en/stable/",
                               license=PSF)
        ]
