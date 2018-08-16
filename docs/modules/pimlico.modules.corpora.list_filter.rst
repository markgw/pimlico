Corpus document list filter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.list_filter

+------------+-------------------------------------+
| Path       | pimlico.modules.corpora.list_filter |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Similar to :mod:pimlico.modules.corpora.split, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| corpus | **invalid input type specification** |
+--------+--------------------------------------+
| list   | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| set1 | **invalid output type specification** |
+------+---------------------------------------+
| set2 | **invalid output type specification** |
+------+---------------------------------------+

