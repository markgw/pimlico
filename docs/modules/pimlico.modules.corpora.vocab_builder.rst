Corpus vocab builder
~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_builder

+------------+---------------------------------------+
| Path       | pimlico.modules.corpora.vocab_builder |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Builds a dictionary (or vocabulary) for a tokenized corpus. This is a data structure that assigns an integer
ID to every distinct word seen in the corpus, optionally applying thresholds so that some words are left out.

Similar to :mod:`pimlico.modules.features.vocab_builder`, which builds two vocabs, one for terms and one for
features.


Inputs
======

+------+-------------------------------------+
| Name | Type(s)                             |
+======+=====================================+
| text | TarredCorpus<TokenizedDocumentType> |
+------+-------------------------------------+

Outputs
=======

+-------+---------------------------------------------------+
| Name  | Type(s)                                           |
+=======+===================================================+
| vocab | :class:`~pimlico.datatypes.dictionary.Dictionary` |
+-------+---------------------------------------------------+

Options
=======

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name      | Description                                                                                                                                                                           | Type                            |
+===========+=======================================================================================================================================================================================+=================================+
| threshold | Minimum number of occurrences required of a term to be included                                                                                                                       | int                             |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| max_prop  | Include terms that occur in max this proportion of documents                                                                                                                          | float                           |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| include   | Ensure that certain words are always included in the vocabulary, even if they don't make it past the various filters, or are never seen in the corpus. Give as a comma-separated list | comma-separated list of strings |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| limit     | Limit vocab size to this number of most common entries (after other filters)                                                                                                          | int                             |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

