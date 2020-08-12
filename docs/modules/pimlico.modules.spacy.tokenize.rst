Tokenizer
~~~~~~~~~

.. py:module:: pimlico.modules.spacy.tokenize

+------------+--------------------------------+
| Path       | pimlico.modules.spacy.tokenize |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Tokenization using spaCy.


Inputs
======

+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                        |
+======+================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TextDocumentType <pimlico.datatypes.corpora.data_points.TextDocumentType>`> |
+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                |
+===========+========================================================================================================================================================================+
| documents | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+---------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name    | Description                                                                                                                                                                                                      | Type   |
+=========+==================================================================================================================================================================================================================+========+
| model   | spaCy model to use. This may be a name of a standard spaCy model or a path to the location of a trained model on disk, if on_disk=T. If it's not a path, the spaCy download command will be run before execution | string |
+---------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| on_disk | Load the specified model from a location on disk (the model parameter gives the path)                                                                                                                            | bool   |
+---------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_spacy_tokenizer_module]
   type=pimlico.modules.spacy.tokenize
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_spacy_tokenizer_module]
   type=pimlico.modules.spacy.tokenize
   input_text=module_a.some_output
   model=en_core_web_sm
   on_disk=T

Example pipelines
=================

This module is used by the following :ref:`example pipelines <example-pipelines>`. They are examples of how the module can be used together with other modules in a larger pipeline.

 * :ref:`example-pipeline-train-tms-example`
 * :ref:`example-pipeline-custom-module-example`

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-spacy-tokenize.conf`

