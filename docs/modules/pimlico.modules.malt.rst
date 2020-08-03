Malt dependency parser
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.malt

+------------+----------------------+
| Path       | pimlico.modules.malt |
+------------+----------------------+
| Executable | yes                  |
+------------+----------------------+

Runs the Malt dependency parser.

Malt is a Java tool, so we use a Py4J wrapper.

Input is supplied as word annotations (which are converted to CoNLL format for
input to the parser). These must include at least each word (field 'word')
and its POS tag (field 'pos'). If a 'lemma' field is supplied, that will
also be used.

The fields in the output contain all of the word features provided by the
parser's output. Some may be ``None`` if they are empty in the parser output.
All the fields in the input (which always include ``word`` and ``pos`` at least)
are also output.


Inputs
======

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                                   |
+===========+===========================================================================================================================================================================================+
| documents | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`WordAnnotationsDocumentType <pimlico.datatypes.corpora.word_annotations.WordAnnotationsDocumentType>`> |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+-------------------------------------------------------------------------------+
| Name   | Type(s)                                                                       |
+========+===============================================================================+
| parsed | :class:`AddAnnotationField <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+-------------------------------------------------------------------------------+


Options
=======

+-------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                                                                                              | Type   |
+=======+==========================================================================================================================================================================================================+========+
| model | Filename of parsing model, or path to the file. If just a filename, assumed to be Malt models dir (models/malt). Default: engmalt.linear-1.7.mco, which can be acquired by 'make malt' in the models dir | string |
+-------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_malt_module]
   type=pimlico.modules.malt
   input_documents=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_malt_module]
   type=pimlico.modules.malt
   input_documents=module_a.some_output
   model=engmalt.linear-1.7.mco

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-malt-parse.conf`

