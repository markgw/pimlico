.. _test-config-gensim-lda_coherence.conf:

lda\_coherence
~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Compute coherence of trained topics over a reference dataset
   #
   # The topic model was trained by the LDA training test pipeline and
   # its topics' top words have been extracted by the top words test pipeline.
   #
   # The "reference set" is the small test tokenized dataset.
   
   [pipeline]
   name=lda_coherence
   release=latest
   
   # Load top words for the topics
   [top_words]
   type=pimlico.datatypes.gensim.TopicsTopWords
   dir=%(test_data_dir)s/datasets/gensim/lda_top_words
   
   # Load vocabulary (same as used to train the model)
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab_ubuntu
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   # Run coherence evaluation
   [coherence]
   type=pimlico.modules.gensim.coherence
   input_topics_top_words=top_words
   input_corpus=europarl
   input_vocab=vocab
   coherence=c_npmi


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.gensim.coherence`
    

