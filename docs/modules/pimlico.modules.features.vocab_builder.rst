Term-feature corpus vocab builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.features.vocab_builder

+------------+----------------------------------------+
| Path       | pimlico.modules.features.vocab_builder |
+------------+----------------------------------------+
| Executable | yes                                    |
+------------+----------------------------------------+

.. todo::

   Document this module


Inputs
======

+---------------+-----------------------------------------------------------------------------------+
| Name          | Type(s)                                                                           |
+===============+===================================================================================+
| term_features | :class:`TermFeatureListCorpus <pimlico.datatypes.features.TermFeatureListCorpus>` |
+---------------+-----------------------------------------------------------------------------------+

Outputs
=======

+---------------+---------------------------------------------------+
| Name          | Type(s)                                           |
+===============+===================================================+
| term_vocab    | :class:`~pimlico.datatypes.dictionary.Dictionary` |
+---------------+---------------------------------------------------+
| feature_vocab | :class:`~pimlico.datatypes.dictionary.Dictionary` |
+---------------+---------------------------------------------------+

Options
=======

+-------------------+------------------------------------------------------------------------------+-------+
| Name              | Description                                                                  | Type  |
+===================+==============================================================================+=======+
| feature_limit     | Limit vocab size to this number of most common entries (after other filters) | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| feature_max_prop  | Include features that occur in max this proportion of documents              | float |
+-------------------+------------------------------------------------------------------------------+-------+
| feature_threshold | Minimum number of occurrences required of a feature to be included           | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| term_limit        | Limit vocab size to this number of most common entries (after other filters) | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| term_max_prop     | Include terms that occur in max this proportion of documents                 | float |
+-------------------+------------------------------------------------------------------------------+-------+
| term_threshold    | Minimum number of occurrences required of a term to be included              | int   |
+-------------------+------------------------------------------------------------------------------+-------+

