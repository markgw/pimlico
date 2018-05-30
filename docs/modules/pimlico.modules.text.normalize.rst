Normalize tokenized text
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.normalize

+------------+--------------------------------+
| Path       | pimlico.modules.text.normalize |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Perform text normalization on tokenized documents.

Currently, this includes only case normalization (to upper or lower case). In
the future, more normalization operations may be added.


Inputs
======

+--------+-------------------------------------+
| Name   | Type(s)                             |
+========+=====================================+
| corpus | TarredCorpus<TokenizedDocumentType> |
+--------+-------------------------------------+

Outputs
=======

+--------+-------------------------------------------------------+
| Name   | Type(s)                                               |
+========+=======================================================+
| corpus | :class:`~pimlico.datatypes.tokenized.TokenizedCorpus` |
+--------+-------------------------------------------------------+

Options
=======

+------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name | Description                                                                                                             | Type                   |
+======+=========================================================================================================================+========================+
| case | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation | 'upper', 'lower' or '' |
+------+-------------------------------------------------------------------------------------------------------------------------+------------------------+

