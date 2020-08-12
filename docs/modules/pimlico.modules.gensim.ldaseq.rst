LDA\-seq \(DTM\) trainer
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.ldaseq

+------------+-------------------------------+
| Path       | pimlico.modules.gensim.ldaseq |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

Trains DTM using Gensim's `DTM implementation <https://radimrehurek.com/gensim/models/ldaseqmodel.html>`_.

Documents in the input corpus should be accompanied by an aligned corpus
of string labels, where each time slice is represented by a label. The
slices should be ordered, so all instances of a given label should be
in sequence.


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
| vocab  | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>`                                                                                                           |
+--------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+--------------------------------------------------------------------+
| Name  | Type(s)                                                            |
+=======+====================================================================+
| model | :class:`ldaseq_model <pimlico.datatypes.gensim.GensimLdaSeqModel>` |
+-------+--------------------------------------------------------------------+


Options
=======

+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name                   | Description                                                                                                                                                                                                                                        | Type                            |
+========================+====================================================================================================================================================================================================================================================+=================================+
| alphas                 | The prior probability for the model                                                                                                                                                                                                                | float                           |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| chain_variance         | Gaussian parameter defined in the beta distribution to dictate how the beta values evolve over time.                                                                                                                                               | float                           |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| chunksize              | Model's chunksize parameter. Chunk size to use for distributed/multicore computing. Default: 2000.                                                                                                                                                 | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| em_max_iter            | Maximum number of iterations until converge of the Expectation-Maximization algorithm                                                                                                                                                              | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| em_min_iter            | Minimum number of iterations until converge of the Expectation-Maximization algorithm                                                                                                                                                              | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| ignore_terms           | Ignore any of these terms in the bags of words when iterating over the corpus to train the model. Typically, you'll want to include an OOV term here if your corpus has one, and any other special terms that are not part of a document's content | comma-separated list of strings |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| lda_inference_max_iter | Maximum number of iterations in the inference step of the LDA training. Default: 25                                                                                                                                                                | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| num_topics             | Number of topics for the trained model to have. Default: 100                                                                                                                                                                                       | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| passes                 | Number of passes over the corpus for the initial LDA model. Default: 10                                                                                                                                                                            | int                             |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| tfidf                  | Transform word counts using TF-IDF when presenting documents to the model for training. Default: False                                                                                                                                             | bool                            |
+------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_ldaseq_trainer_module]
   type=pimlico.modules.gensim.ldaseq
   input_corpus=module_a.some_output
   input_labels=module_a.some_output
   input_vocab=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_ldaseq_trainer_module]
   type=pimlico.modules.gensim.ldaseq
   input_corpus=module_a.some_output
   input_labels=module_a.some_output
   input_vocab=module_a.some_output
   alphas=0.01
   chain_variance=0.01
   chunksize=100
   em_max_iter=20
   em_min_iter=6
   ignore_terms=
   lda_inference_max_iter=25
   num_topics=100
   passes=10
   tfidf=F

Example pipelines
=================

This module is used by the following :ref:`example pipelines <example-pipelines>`. They are examples of how the module can be used together with other modules in a larger pipeline.

 * :ref:`example-pipeline-train-tms-example`

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-gensim-dtm_train.conf`

