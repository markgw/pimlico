20 Newsgroups fetcher \(sklearn\)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.text.20newsgroups.sklearn_download

+------------+----------------------------------------------------------+
| Path       | pimlico.modules.input.text.20newsgroups.sklearn_download |
+------------+----------------------------------------------------------+
| Executable | yes                                                      |
+------------+----------------------------------------------------------+

Input reader to fetch the 20 Newsgroups dataset from Sklearn.
See: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_20newsgroups.html

The original data can be downloaded from http://qwone.com/~jason/20Newsgroups/.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

No inputs

Outputs
=======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                              |
+========+======================================================================================================================================================================+
| text   | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| labels | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerDocumentType <pimlico.datatypes.corpora.ints.IntegerDocumentType>`>        |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name         | Description                                                                                                                                                                                                 | Type                            |
+==============+=============================================================================================================================================================================================================+=================================+
| limit        | Truncate corpus                                                                                                                                                                                             | int                             |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| random_state | Determines random number generation for dataset shuffling. Pass an int for reproducible output across multiple runs                                                                                         | int                             |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| remove       | May contain any subset of (‘headers’, ‘footers’, ‘quotes’). Each of these are kinds of text that will be detected and removed from the newsgroup posts, preventing classifiers from overfitting on metadata | comma-separated list of strings |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| shuffle      | Whether or not to shuffle the data: might be important for models that make the assumption that the samples are independent and identically distributed (i.i.d.), such as stochastic gradient descent       | bool                            |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| subset       | Select the dataset to load: ‘train’ for the training set, ‘test’ for the test set, ‘all’ for both, with shuffled ordering                                                                                   | 'train', 'test' or 'all'        |
+--------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_20ng_fetcher_module]
   type=pimlico.modules.input.text.20newsgroups.sklearn_download
   

This example usage includes more options.

.. code-block:: ini
   
   [my_20ng_fetcher_module]
   type=pimlico.modules.input.text.20newsgroups.sklearn_download
   limit=0
   random_state=0
   remove=text,text,...
   shuffle=T
   subset=train

