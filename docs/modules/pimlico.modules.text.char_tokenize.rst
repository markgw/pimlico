Text to character level
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.char_tokenize

+------------+------------------------------------+
| Path       | pimlico.modules.text.char_tokenize |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Filter to treat text data as character-level tokenized data. This makes it simple to
train character-level models, since the output appears exactly like a tokenized
document, where each token is a single character. You can then feed it into any
module that expects tokenized text.


Inputs
======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                        |
+========+================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TextDocumentType <pimlico.datatypes.corpora.data_points.TextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                                  |
+========+==========================================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`CharacterTokenizedDocumentType <pimlico.datatypes.corpora.tokenized.CharacterTokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_char_tokenize_module]
   type=pimlico.modules.text.char_tokenize
   input_corpus=module_a.some_output
   

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-text-char_tokenize.conf`