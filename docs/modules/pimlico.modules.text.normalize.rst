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

+--------+--------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                          |
+========+==================================================================================================+
| corpus | :class:`grouped_corpus<TokenizedDocumentType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+--------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+---------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                           |
+========+===================================================================================================+
| corpus | :class:`~pimlico.datatypes.corpora.grouped.GroupedCorpus <grouped_corpus<TokenizedDocumentType>>` |
+--------+---------------------------------------------------------------------------------------------------+

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

