# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import zip
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.files import NamedFileCollectionWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_collections = self.info.get_input("files", always_list=True)

        output_datatype = self.info.get_output_datatype("files")[1]

        class OutputWriter(NamedFileCollectionWriter):
            filenames = output_datatype.filenames

        with OutputWriter(self.info.get_absolute_output_dir("files")) as writer:
            for input_collection, filename_mapping in zip(input_collections, output_datatype.collection_mappings):
                for filename in input_collection.filenames:
                    writer.write_file(filename_mapping[filename], input_collection.read_file(filename))
