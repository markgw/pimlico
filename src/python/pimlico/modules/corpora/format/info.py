# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Corpus formatter

Pimlico provides a data browser to make it easy to view documents in a tarred document corpus. Some datatypes
provide a way to format the data for display in the browser, whilst others provide multiple formatters that
display the data in different ways.

This module allows you to use this formatting functionality to output the formatted data as a corpus. Since the
formatting operations are designed for display, this is generally only useful to output the data for human
consumption.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.old_datatypes.tar import TarredCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "format"
    module_readable_name = "Human-readable formatting"
    module_inputs = [("corpus", TarredCorpus)]
    module_outputs = [("formatted", TarredCorpus)]
    module_options = {
        "formatter": {
            "help": "Fully qualified class name of a formatter to use to format the data. If not specified, the "
                    "default formatter is used, which uses the datatype's browser_display attribute if available, "
                    "or falls back to just converting documents to unicode",
        },
    }
