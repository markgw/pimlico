.. _test-config-gensim-dtm_train.conf:

dtm\_train
~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Train a DTM model on a pre-prepared word-ID corpus and document labels
   #
   # For a fuller example (on which this test is based), see
   # :doc:`the topic model training example </example_config/topic_modelling.train_tms>`.
   
   [pipeline]
   name=dtm_train
   release=latest
   
   # Load word IDs
   [ids]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=IntegerListsDocumentType
   dir=%(test_data_dir)s/datasets/corpora/ids_ubuntu
   
   # Load slice labels
   [labels]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=LabelDocumentType
   dir=%(test_data_dir)s/datasets/corpora/labels_ubuntu
   
   # Load vocabulary
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab_ubuntu
   
   [dtm]
   type=pimlico.modules.gensim.ldaseq
   input_corpus=ids
   input_labels=labels
   input_vocab=vocab
   # Small number of topics: you probably want more in practice
   num_topics=2
   # Speed up training for this test by reducing all passes/iterations to very small values
   em_min_iter=1
   em_max_iter=1
   passes=2
   lda_inference_max_iter=2


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.gensim.ldaseq`
    

