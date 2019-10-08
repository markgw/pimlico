Token frequency counter
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_counter

+------------+---------------------------------------+
| Path       | pimlico.modules.corpora.vocab_counter |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Count the frequency of each token of a vocabulary in a given corpus (most often
the corpus on which the vocabulary was built).

Note that this distribution is not otherwise available along with the vocabulary.
It stores the document frequency counts - how many documents each token appears
in - which may sometimes be a close enough approximation to the actual frequencies.
But, for example, when working with character-level tokens, this estimate will
be very poor.

The output will be a 1D array whose size is the length of the vocabulary, or
the length plus one, if ``oov_excluded=T`` (used if the corpus has been mapped
so that OOVs are represented by the ID ``vocab_size+1``, instead of having a
special token).


Inputs
======

+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                 |
+========+=========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerListsDocumentType <pimlico.datatypes.corpora.ints.IntegerListsDocumentType>`> |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vocab  | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>`                                                                                                           |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------------+------------------------------------------------------------+
| Name         | Type(s)                                                    |
+==============+============================================================+
| distribution | :class:`numpy_array <pimlico.datatypes.arrays.NumpyArray>` |
+--------------+------------------------------------------------------------+


Options
=======

+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------+
| Name         | Description                                                                                                                                   | Type |
+==============+===============================================================================================================================================+======+
| oov_excluded | Indicates that the corpus has been mapped so that OOVs are represented by the ID vocab_size+1, instead of having a special token in the vocab | bool |
+--------------+-----------------------------------------------------------------------------------------------------------------------------------------------+------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_vocab_counter_module]
   type=pimlico.modules.corpora.vocab_counter
   input_corpus=module_a.some_output
   input_vocab=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_vocab_counter_module]
   type=pimlico.modules.corpora.vocab_counter
   input_corpus=module_a.some_output
   input_vocab=module_a.some_output
   oov_excluded=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-vocab_counter.conf`