Normalize tokenized text
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.normalize

+------------+--------------------------------+
| Path       | pimlico.modules.text.normalize |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Perform text normalization on tokenized documents.

Currently, this includes the following:

 - case normalization (to upper or lower case)
 - blank line removal
 - empty sentence removal
 - punctuation removal
 - removal of words that contain only punctuation
 - numerical character removal
 - minimum word length filter

In the future, more normalization operations may be added.


Inputs
======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                |
+========+========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                |
+========+========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name              | Description                                                                                                                                          | Type                   |
+===================+======================================================================================================================================================+========================+
| case              | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation                              | 'upper', 'lower' or '' |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| min_word_length   | Remove any words shorter than this. Default: 0 (don't do anything)                                                                                   | int                    |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_empty      | Skip over any empty sentences (i.e. blank lines). Applied after other processing, so this will remove sentences that are left empty by other filters | bool                   |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_nums       | Remove numeric characters                                                                                                                            | bool                   |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_only_punct | Skip over any sentences that are empty if punctuation is ignored                                                                                     | bool                   |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_punct      | Remove punctuation from all tokens and then remove the whole token if nothing's left                                                                 | bool                   |
+-------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_normalize_module]
   type=pimlico.modules.text.normalize
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_normalize_module]
   type=pimlico.modules.text.normalize
   input_corpus=module_a.some_output
   case=
   min_word_length=0
   remove_empty=F
   remove_nums=F
   remove_only_punct=F
   remove_punct=F

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-text-normalize.conf`