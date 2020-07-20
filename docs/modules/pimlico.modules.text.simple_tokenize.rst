Simple tokenization
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.simple_tokenize

+------------+--------------------------------------+
| Path       | pimlico.modules.text.simple_tokenize |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Tokenize raw text using simple splitting.

This is useful where either you don't mind about the quality of the tokenization and
just want to test something quickly, or text is actually already tokenized, but stored
as a raw text datatype.

If you want to do proper tokenization, consider either the CoreNLP or OpenNLP core
modules.


Inputs
======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                        |
+========+================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TextDocumentType <pimlico.datatypes.corpora.data_points.TextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                |
+========+========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+----------+-------------------------------------------------+--------+
| Name     | Description                                     | Type   |
+==========+=================================================+========+
| splitter | Character or string to split on. Default: space | string |
+----------+-------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_simple_tokenize_module]
   type=pimlico.modules.text.simple_tokenize
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_simple_tokenize_module]
   type=pimlico.modules.text.simple_tokenize
   input_corpus=module_a.some_output
   splitter= 

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-text-simple_tokenize.conf`