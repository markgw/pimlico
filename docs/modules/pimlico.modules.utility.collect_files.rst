Collect files
~~~~~~~~~~~~~

.. py:module:: pimlico.modules.utility.collect_files

+------------+---------------------------------------+
| Path       | pimlico.modules.utility.collect_files |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Collect files output from different modules.

A simple convenience module to make it easier to inspect output by putting it all
in one place.

Files are either collected into subdirectories or renamed to avoid
clashes.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-------+---------------------------------------------------------------------------------------------------------------------------------------+
| Name  | Type(s)                                                                                                                               |
+=======+=======================================================================================================================================+
| files | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`named_file_collection <pimlico.datatypes.files.NamedFileCollection>` |
+-------+---------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+-----------------------------------------------------------------------------------------------------------------+
| Name  | Type(s)                                                                                                         |
+=======+=================================================================================================================+
| files | :class:`collected_named_file_collection <pimlico.modules.utility.collect_files.info.MappedNamedFileCollection>` |
+-------+-----------------------------------------------------------------------------------------------------------------+

Options
=======

+---------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Name    | Description                                                                                                                                                                               | Type               |
+=========+===========================================================================================================================================================================================+====================+
| names   | List of string identifiers to use to distinguish the files from different sources, either used as subdirectory names or filename prefixes. If not given, integer ids will be used instead | absolute file path |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| subdirs | Use subdirectories to collect the files from different sources, rather than renaming each file. By default, a prefix is added to the filenames                                            | bool               |
+---------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_collect_files_module]
   type=pimlico.modules.utility.collect_files
   input_files=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_collect_files_module]
   type=pimlico.modules.utility.collect_files
   input_files=module_a.some_output
   names=path1,path2,...
   subdirs=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-collect_files.conf`