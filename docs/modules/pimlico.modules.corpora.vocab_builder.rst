Term-feature corpus vocab builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

+------+------------------------------------------------------------------------+
| Name | Type(s)                                                                |
+======+========================================================================+
| text | :class:`TokenizedCorpus <pimlico.datatypes.tokenized.TokenizedCorpus>` |
+------+------------------------------------------------------------------------+

Outputs
=======

+-------+---------------------------------------------------+
| Name  | Type(s)                                           |
+=======+===================================================+
| vocab | :class:`~pimlico.datatypes.dictionary.Dictionary` |
+-------+---------------------------------------------------+

Options
=======

+-----------+------------------------------------------------------------------------------+-------+
| Name      | Description                                                                  | Type  |
+===========+==============================================================================+=======+
| limit     | Limit vocab size to this number of most common entries (after other filters) | int   |
+-----------+------------------------------------------------------------------------------+-------+
| max_prop  | Include terms that occur in max this proportion of documents                 | float |
+-----------+------------------------------------------------------------------------------+-------+
| threshold | Minimum number of occurrences required of a term to be included              | int   |
+-----------+------------------------------------------------------------------------------+-------+

