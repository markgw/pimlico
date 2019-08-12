# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import zip

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_collections = self.info.get_input("files", always_list=True)
        self.log.info("Collecting files from {} input modules".format(len(input_collections)))

        with self.info.get_output_writer("files") as writer:
            if writer.datatype.collection_mappings is not None and len(writer.datatype.collection_mappings):
                self.log.info("Apply filename mapping: {}".format(
                    "; ".join(
                        ", ".join(
                            "{}->{}".format(src, trg) for src, trg in mapping.items())
                        for mapping in writer.datatype.collection_mappings)
                ))

            for input_collection, filename_mapping in zip(input_collections, writer.datatype.collection_mappings):
                for filename in input_collection.filenames:
                    writer.write_file(filename_mapping[filename], input_collection.read_file(filename))
