# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Alias a datatype coming from the output of another module.

Used to assign a handy identifier to the output of a module, so that we can just refer to this
alias module later in the pipeline and use its default output. This can help make for a more
readable pipeline config.

For example, say we use :mod:`~pimlico.modules.corpora.split` to split a dataset into two random
subsets. The two splits can be accessed by referring to the two outputs of that module:
`split_module.set1` and `split_module.set2`. However, it's easy to lose track of what these splits
are supposed to be used for, so we might want to give them names:

.. code-block:: ini

   [split_module]
   type=pimlico.modules.corpora.split
   set1_size=0.2

   [test_set]
   type=pimlico.modules.utility.alias
   input=split_module.set1

   [training_set]
   type=pimlico.modules.utility.alias
   input=split_module.set2

   [training_routine]
   type=...
   input_corpus=training_set

Note the difference between using this module and using the special `alias` module type. The `alias`
type creates an alias for a whole module, allowing you to refer to all of its outputs, inherit its settings,
and anything else you could do with the original module name. This module, however, provides an alias for
exactly one output of a module and generates a module instance of its own in the pipeline (albeit a
filter module).

.. todo::

   Update to new datatypes system and add test pipeline

"""

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.base import PimlicoDatatype, TypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "alias"
    module_readable_name = "Module output alias"
    module_executable = False
    module_inputs = [("input", PimlicoDatatype)]
    module_outputs = [("output", TypeFromInput())]

    def instantiate_output_datatype(self, output_name, output_datatype):
        return self.get_input("input")
