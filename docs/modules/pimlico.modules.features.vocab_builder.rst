!! Term-feature corpus vocab builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.features.vocab_builder

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+----------------------------------------+
| Path       | pimlico.modules.features.vocab_builder |
+------------+----------------------------------------+
| Executable | yes                                    |
+------------+----------------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+---------------+--------------------------------------+
| Name          | Type(s)                              |
+===============+======================================+
| term_features | **invalid input type specification** |
+---------------+--------------------------------------+

Outputs
=======

+---------------+---------------------------------------+
| Name          | Type(s)                               |
+===============+=======================================+
| term_vocab    | **invalid output type specification** |
+---------------+---------------------------------------+
| feature_vocab | **invalid output type specification** |
+---------------+---------------------------------------+

Options
=======

+-------------------+------------------------------------------------------------------------------+-------+
| Name              | Description                                                                  | Type  |
+===================+==============================================================================+=======+
| feature_limit     | Limit vocab size to this number of most common entries (after other filters) | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| feature_max_prop  | Include features that occur in max this proportion of documents              | float |
+-------------------+------------------------------------------------------------------------------+-------+
| term_max_prop     | Include terms that occur in max this proportion of documents                 | float |
+-------------------+------------------------------------------------------------------------------+-------+
| term_threshold    | Minimum number of occurrences required of a term to be included              | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| feature_threshold | Minimum number of occurrences required of a feature to be included           | int   |
+-------------------+------------------------------------------------------------------------------+-------+
| term_limit        | Limit vocab size to this number of most common entries (after other filters) | int   |
+-------------------+------------------------------------------------------------------------------+-------+

