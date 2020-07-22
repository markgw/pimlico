Constituency parser
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.parse

+------------+-------------------------------+
| Path       | pimlico.modules.opennlp.parse |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

Constituency parsing using OpenNLP's tools.

We run OpenNLP in the background using a Py4J wrapper, just as with the other
OpenNLP wrappers.

The output format is not yet ideal: currently we produce documents consisting of a
list of strings, each giving the OpenNLP tree output for a sentence. It would be
better to use a standard constituency tree datatype that can be used generically
as input to any modules required tree input. For now, if you write a module taking
input from the parser, it will itself need to process the strings from the OpenNLP
parser output.


Inputs
======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                |
+===========+========================================================================================================================================================================+
| documents | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name  | Type(s)                                                                                                                                                                                    |
+=======+============================================================================================================================================================================================+
| trees | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`OpenNLPTreeStringsDocumentType <pimlico.datatypes.corpora.parse.trees.OpenNLPTreeStringsDocumentType>`> |
+-------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+-------+------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                              | Type   |
+=======+==========================================================================================================================================+========+
| model | Parser model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/) | string |
+-------+------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_opennlp_parser_module]
   type=pimlico.modules.opennlp.parse
   input_documents=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_opennlp_parser_module]
   type=pimlico.modules.opennlp.parse
   input_documents=module_a.some_output
   model=en-parser-chunking.bin

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-opennlp-parse.conf`