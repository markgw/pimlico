# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Copy a file

Simple utility for copying a file (which presumably comes from the output of another module) into a particular
location. Useful for collecting together final output at the end of a pipeline.

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.base import MultipleInputs
from pimlico.old_datatypes.files import File


class ModuleInfo(BaseModuleInfo):
    module_type_name = "copy_file"
    module_readable_name = "Copy file"
    module_inputs = [("source", MultipleInputs(File))]
    module_options = {
        "target_dir": {
            "help": "Path to directory into which the file should be copied. Will be created if it doesn't exist",
            "required": True,
        },
        "target_name": {
            "help": "Name to rename the target file to. If not given, it will have the same name as the source file. "
                    "Ignored if there's more than one input file",
        }
    }
