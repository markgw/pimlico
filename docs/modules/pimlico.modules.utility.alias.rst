!! Module output alias
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.utility.alias

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-------------------------------+
| Path       | pimlico.modules.utility.alias |
+------------+-------------------------------+
| Executable | no                            |
+------------+-------------------------------+

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


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+-------+--------------------------------------+
| Name  | Type(s)                              |
+=======+======================================+
| input | **invalid input type specification** |
+-------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| output | **invalid output type specification** |
+--------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_alias_module]
   type=pimlico.modules.utility.alias
   input_input=module_a.some_output
   

