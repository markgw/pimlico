Copy file
~~~~~~~~~

.. py:module:: pimlico.modules.utility.copy_file

+------------+-----------------------------------+
| Path       | pimlico.modules.utility.copy_file |
+------------+-----------------------------------+
| Executable | yes                               |
+------------+-----------------------------------+

Copy a file

Simple utility for copying a file (which presumably comes from the output of another module) into a particular
location. Useful for collecting together final output at the end of a pipeline.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| source | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+-----------+---------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                     |
+===========+=============================================================================================+
| documents | :class:`~pimlico.datatypes.corpora.grouped.GroupedCorpus <grouped_corpus<RawDocumentType>>` |
+-----------+---------------------------------------------------------------------------------------------+

Options
=======

+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name        | Description                                                                                                                                 | Type   |
+=============+=============================================================================================================================================+========+
| target_name | Name to rename the target file to. If not given, it will have the same name as the source file. Ignored if there's more than one input file | string |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+
| target_dir  | (required) Path to directory into which the file should be copied. Will be created if it doesn't exist                                      | string |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+

