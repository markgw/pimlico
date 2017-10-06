# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Group the files of a multi-file iterable corpus into tar archives. This is a
standard thing to do at the start of the pipeline, since it's a handy way to
store many (potentially small) files without running into filesystem problems.

The files are simply grouped linearly into a series of tar archives such that
each (apart from the last) contains the given number.

After grouping documents in this way, document map modules can be called on the corpus and the
grouping will be preserved as the corpus passes through the pipeline.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import IterableCorpus
from pimlico.datatypes.tar import TarredCorpus
from pimlico.modules.corpora.tar_filter.info import TarredCorpusWithDocumentTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "tar"
    module_readable_name = "Tar archive grouper"
    module_inputs = [("documents", IterableCorpus)]
    module_outputs = [("documents", TarredCorpusWithDocumentTypeFromInput())]
    module_options = {
        "archive_size": {
            "help": "Number of documents to include in each archive (default: 1k)",
            "default": 1000,
        },
        "archive_basename": {
            "help": "Base name to use for archive tar files. The archive number is appended to this. "
                    "(Default: 'archive')",
            "default": "archive",
        },
    }
