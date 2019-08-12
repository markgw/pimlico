# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Collect files output from different modules.

A simple convenience module to make it easier to inspect output by putting it all
in one place.

Files are either collected into subdirectories or renamed to avoid
clashes.

"""
import os
import warnings
from builtins import zip, range, super

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool, comma_separated_strings
from pimlico.datatypes import DynamicOutputDatatype
from pimlico.datatypes.base import MultipleInputs
from pimlico.datatypes.files import NamedFileCollection


class MappedNamedFileCollection(NamedFileCollection):
    """
    Same as NamedFileCollection, but provides access to a filename mapping
    that was applied to produce the collected filenames.

    """
    def __init__(self, *args, **kwargs):
        self.collection_mappings = kwargs.pop("collection_mappings", {})
        super().__init__(*args, **kwargs)


class CollectedFiles(DynamicOutputDatatype):
    datatype_name = "collected_named_file_collection"

    def get_datatype(self, module_info):
        input_collections = module_info.get_input_datatype("files", always_list=True)

        if module_info.options["names"] is None:
            # No distinguishing names given: use int ids instead
            collection_names = ["{:02d}".format(i) for i in range(len(input_collections))]
        else:
            # Check we've got the right number of names
            collection_names = module_info.options["names"]
            if len(collection_names) < len(input_collections):
                raise ValueError("got too few names ({}) to distinguish {} file collections".format(
                    len(collection_names), len(input_collections)
                ))
            elif len(collection_names) > len(input_collections):
                # Not a problem if we've got too many names, but it's probably a sign of a mistake, so warn
                warnings.warn("got more file collection names ({}) than needed to distinguish {} collections".format(
                    len(collection_names), len(input_collections)
                ))

        # Build the mapping from input files to output paths
        filename_mappings = []
        new_filenames = []
        for input_collection, collection_name in zip(input_collections, collection_names):
            if module_info.options["subdirs"]:
                filename_mapping = dict(
                    (filename, os.path.join(collection_name, filename)) for filename in input_collection.filenames
                )
            else:
                filename_mapping = dict(
                    (filename, "{}_{}".format(collection_name, filename)) for filename in input_collection.filenames
                )
            filename_mappings.append(filename_mapping)
            new_filenames.extend(list(filename_mapping.values()))

        return MappedNamedFileCollection(filenames=new_filenames, collection_mappings=filename_mappings)

    def get_base_datatype(self):
        return MappedNamedFileCollection()


class ModuleInfo(BaseModuleInfo):
    module_type_name = "collect_files"
    module_readable_name = "Collect files"
    module_inputs = [("files", MultipleInputs(NamedFileCollection()))]
    module_outputs = [("files", CollectedFiles())]
    module_options = {
        "subdirs": {
            "help": "Use subdirectories to collect the files from different sources, rather than renaming each "
                    "file. By default, a prefix is added to the filenames",
            "type": str_to_bool,
        },
        "names": {
            "help": "List of string identifiers to use to distinguish the files from different sources, either "
                    "used as subdirectory names or filename prefixes. If not given, integer ids will be used "
                    "instead",
            "type": comma_separated_strings,
        }
    }