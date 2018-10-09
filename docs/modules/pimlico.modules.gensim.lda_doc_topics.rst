LDA document topic analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.lda_doc_topics

+------------+---------------------------------------+
| Path       | pimlico.modules.gensim.lda_doc_topics |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Takes a trained LDA model and produces the topic vector for every document in a corpus.

The corpus is given as integer lists documents, which are the integer IDs of the words
in each sentence of each document. It is assumed that the corpus uses the same vocabulary
to map to integer IDs as the LDA model's training corpus, so no further mapping needs to
be done.

.. todo::

   Add test pipeline and test


Inputs
======

+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                 |
+========+=========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerListsDocumentType <pimlico.datatypes.corpora.ints.IntegerListsDocumentType>`> |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| model  | :class:`lda_model <pimlico.datatypes.gensim.GensimLdaModel>`                                                                                                            |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                                                       |
+=========+===============================================================================================================================================================+
| vectors | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`VectorDocumentType <pimlico.datatypes.corpora.floats.VectorDocumentType>`> |
+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_lda_doc_topics_module]
   type=pimlico.modules.gensim.lda_doc_topics
   input_corpus=module_a.some_output
   input_model=module_a.some_output
   

