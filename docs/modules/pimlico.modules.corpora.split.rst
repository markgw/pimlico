Corpus subset
~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.split

+------------+-------------------------------+
| Path       | pimlico.modules.corpora.split |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

Split a tarred corpus into two subsets. Useful for dividing a dataset into training and test subsets.
The output datasets have the same type as the input. The documents to put in each set are selected randomly.
Running the module multiple times will give different splits.

Note that you can use this multiple times successively to split more than two ways. For example, say you wanted
a training set with 80% of your data, a dev set with 10% and a test set with 10%, split it first into training
and non-training 80-20, then split the non-training 50-50 into dev and test.

The module also outputs a list of the document names that were included in the first set. Optionally, it outputs
the same thing for the second input too. Note that you might prefer to only store this list for the smaller set:
e.g. in a training-test split, store only the test document list, as the training list will be much larger. In such
a case, just put the smaller set first and don't request the optional output `doc_list2`.


Inputs
======

+--------+------------------------------------------------------------+
| Name   | Type(s)                                                    |
+========+============================================================+
| corpus | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+--------+------------------------------------------------------------+

Outputs
=======

+-----------+----------------------------------------------------------------------------------+
| Name      | Type(s)                                                                          |
+===========+==================================================================================+
| set1      | :class:`same as input corpus <pimlico.modules.corpora.split.info.TypeFromInput>` |
+-----------+----------------------------------------------------------------------------------+
| set2      | :class:`same as input corpus <pimlico.modules.corpora.split.info.TypeFromInput>` |
+-----------+----------------------------------------------------------------------------------+
| doc_list1 | :class:`~pimlico.datatypes.base.StringList`                                      |
+-----------+----------------------------------------------------------------------------------+


Optional
--------

+-----------+---------------------------------------------+
| Name      | Type(s)                                     |
+===========+=============================================+
| doc_list2 | :class:`~pimlico.datatypes.base.StringList` |
+-----------+---------------------------------------------+

Options
=======

+-----------+-------------------------------------------------------------------------------------------+-------+
| Name      | Description                                                                               | Type  |
+===========+===========================================================================================+=======+
| set1_size | Proportion of the corpus to put in the first set, float between 0.0 and 1.0. Default: 0.2 | float |
+-----------+-------------------------------------------------------------------------------------------+-------+
