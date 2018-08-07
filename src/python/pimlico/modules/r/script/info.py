# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Simple interface to R that just involves running a given R script, first substituting in some paths from the
pipeline, making it easy to pass in data from the output of other modules.

.. todo::

   Update to new datatypes system and add test pipeline

"""

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.base import MultipleInputs, PimlicoDatatype
from pimlico.old_datatypes.files import NamedFile
from pimlico.modules.r.deps import r_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "r_script"
    module_readable_name = "R script executor"
    module_inputs = [("sources", MultipleInputs(PimlicoDatatype))]
    module_outputs = [("output", NamedFile("output.txt"))]
    module_options = {
        "script": {
            "help": "Path to the script to be run. The script itself may include substitutions of the form "
                    "'{{inputX}}', which will be replaced with the absolute path to the data dir of the Xth input, "
                    "and '{{output}}', which will be replaced with the absolute path to the output dir. The latter "
                    "allows the script to output things other than the output file, which always exists and contains "
                    "the full script's output",
            "required": True,
        }
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [r_dependency]
