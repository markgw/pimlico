Normalize raw text
~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.text_normalize

+------------+-------------------------------------+
| Path       | pimlico.modules.text.text_normalize |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Text normalization for raw text documents.

Similar to :mod:`~pimlico.modules.text.normalize` module, but operates on raw text,
not pre-tokenized text, so provides a slightly different set of tools.


Inputs
======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                        |
+========+================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TextDocumentType <pimlico.datatypes.corpora.data_points.TextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                              |
+========+======================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name        | Description                                                                                                             | Type                   |
+=============+=========================================================================================================================+========================+
| blank_lines | Remove all blank lines (after whitespace stripping, if requested)                                                       | bool                   |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| case        | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation | 'upper', 'lower' or '' |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| strip       | Strip whitespace from the start and end of lines                                                                        | bool                   |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_text_normalize_module]
   type=pimlico.modules.text.text_normalize
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_text_normalize_module]
   type=pimlico.modules.text.text_normalize
   input_corpus=module_a.some_output
   blank_lines=T
   case=
   strip=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-text_normalize.conf`