.. _test-config-gensim-lda_train.conf:

dtm\_train
~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Train an LDA model on a pre-prepared word-ID corpus
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
   
   # Load vocabulary
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab_ubuntu
   
   # First train a plain LDA model using Gensim
   [lda]
   type=pimlico.modules.gensim.lda
   input_vocab=vocab
   input_corpus=ids
   tfidf=T
   # Small number of topics: you probably want more in practice
   num_topics=5
   passes=10


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.gensim.lda`
    

