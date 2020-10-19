Text parser
~~~~~~~~~~~

.. py:module:: pimlico.modules.spacy.parse_text

+------------+----------------------------------+
| Path       | pimlico.modules.spacy.parse_text |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

Parsing using spaCy

Entire parsing pipeline from raw text using the same spaCy model.

The word annotations in the output contain the information from the spaCy parser
and the documents are split into sentences following the spaCy's sentence segmentation.

The annotation fields follow those produced by the Malt parser: pos, head and deprel.


Inputs
======

+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                              |
+======+======================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                                   |
+========+===========================================================================================================================================================================================+
| parsed | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`WordAnnotationsDocumentType <pimlico.datatypes.corpora.word_annotations.WordAnnotationsDocumentType>`> |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


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
   
   [my_spacy_text_parser_module]
   type=pimlico.modules.spacy.parse_text
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_spacy_text_parser_module]
   type=pimlico.modules.spacy.parse_text
   input_text=module_a.some_output
   model=en_core_web_sm
   on_disk=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-spacy-parse_text.conf`

