Corpus split
~~~~~~~~~~~~

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

+--------+---------------------------------------------------------------------------+
| Name   | Type(s)                                                                   |
+========+===========================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+---------------------------------------------------------------------------+

Outputs
=======

+-----------+-----------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                       |
+===========+===============================================================================================+
| set1      | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+-----------+-----------------------------------------------------------------------------------------------+
| set2      | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+-----------+-----------------------------------------------------------------------------------------------+
| doc_list1 | :class:`string_list <pimlico.datatypes.core.StringList>`                                      |
+-----------+-----------------------------------------------------------------------------------------------+


Optional
--------

+-----------+----------------------------------------------------------+
| Name      | Type(s)                                                  |
+===========+==========================================================+
| doc_list2 | :class:`string_list <pimlico.datatypes.core.StringList>` |
+-----------+----------------------------------------------------------+


Output groups
=============

The module defines some named output groups, which can be used to refer to collections of outputs at once, as multiple inputs to another module or alternative inputs.

+------------+------------+
| Group name | Outputs    |
+============+============+
| corpora    | set1, set2 |
+------------+------------+


Options
=======

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+
| Name      | Description                                                                                                                                                                                                                       | Type  |
+===========+===================================================================================================================================================================================================================================+=======+
| set1_size | Proportion of the corpus to put in the first set, float between 0.0 and 1.0. If an integer >1 is given, this is treated as the absolute number of documents to put in the first set, rather than a proportion. Default: 0.2 (20%) | float |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_split_module]
   type=pimlico.modules.corpora.split
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_split_module]
   type=pimlico.modules.corpora.split
   input_corpus=module_a.some_output
   set1_size=0.20

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-corpora-split.conf`

