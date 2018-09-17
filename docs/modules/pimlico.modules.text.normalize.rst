Normalize tokenized text
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.normalize

+------------+--------------------------------+
| Path       | pimlico.modules.text.normalize |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Perform text normalization on tokenized documents.

Currently, this includes only the following:

 - case normalization (to upper or lower case)
 - blank line removal
 - empty sentence removal

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

+-------------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name              | Description                                                                                                             | Type                   |
+===================+=========================================================================================================================+========================+
| case              | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation | 'upper', 'lower' or '' |
+-------------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_only_punct | Skip over any sentences that are empty if punctuation is ignored                                                        | bool                   |
+-------------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| remove_empty      | Skip over any empty sentences (i.e. blank lines)                                                                        | bool                   |
+-------------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_normalize_module]
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_normalize_module]
   input_corpus=module_a.some_output
   case=
   remove_only_punct=F
   remove_empty=F

