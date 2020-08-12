LDA\-seq \(DTM\) document topic analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.ldaseq_doc_topics

+------------+------------------------------------------+
| Path       | pimlico.modules.gensim.ldaseq_doc_topics |
+------------+------------------------------------------+
| Executable | yes                                      |
+------------+------------------------------------------+

Takes a trained DTM model and produces the topic vector for every document in a corpus.

The corpus is given as integer lists documents, which are the integer IDs of the words
in each sentence of each document. It is assumed that the corpus uses the same vocabulary
to map to integer IDs as the LDA model's training corpus, so no further mapping needs to
be done.

We also require a corpus of labels to say what time slice each document is in. These
should be from the same set of labels that the DTM model was trained on, so that each
document label can be mapped to a trained slice.

Does not support Python 2 since Gensim has dropped Python 2 support.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                 |
+========+=========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerListsDocumentType <pimlico.datatypes.corpora.ints.IntegerListsDocumentType>`> |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| labels | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`LabelDocumentType <pimlico.datatypes.corpora.strings.LabelDocumentType>`>            |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| model  | :class:`ldaseq_model <pimlico.datatypes.gensim.GensimLdaSeqModel>`                                                                                                      |
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
   
   [my_ldaseq_doc_topics_module]
   type=pimlico.modules.gensim.ldaseq_doc_topics
   input_corpus=module_a.some_output
   input_labels=module_a.some_output
   input_model=module_a.some_output
   

Example pipelines
=================

This module is used by the following :ref:`example pipelines <example-pipelines>`. They are examples of how the module can be used together with other modules in a larger pipeline.

 * :ref:`example-pipeline-train-tms-example`

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-gensim-dtm_infer.conf`

