NP chunk extractor
~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.spacy.extract_nps

+------------+-----------------------------------+
| Path       | pimlico.modules.spacy.extract_nps |
+------------+-----------------------------------+
| Executable | yes                               |
+------------+-----------------------------------+

Extract NP chunks

Performs the full spaCy pipeline including tokenization, sentence
segmentation, POS tagging and parsing and outputs documents containing
only a list of the noun phrase chunks that were found by the parser.

This functionality is provided very conveniently by spaCy's ``Doc.noun_chunks``
after parsing, so this is a light wrapper around spaCy.

The output is presented as a tokenized document. Each sentence in the
document represents a single NP.


Inputs
======

+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                              |
+======+======================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| nps  | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


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
   
   [my_spacy_extract_nps_module]
   type=pimlico.modules.spacy.extract_nps
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_spacy_extract_nps_module]
   type=pimlico.modules.spacy.extract_nps
   input_text=module_a.some_output
   model=en_core_web_sm
   on_disk=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-spacy-extract_nps.conf`

