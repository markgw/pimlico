.. _test-config-gensim-lda_top_words.conf:

lda\_top\_words
~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Extract lists of words from an LDA model
   #
   # These can be used for coherence evaluation.
   
   [pipeline]
   name=lda_top_words
   release=latest
   
   # Load trained model
   [lda]
   type=pimlico.datatypes.gensim.GensimLdaModel
   dir=%(test_data_dir)s/datasets/gensim/lda
   
   # Extract the top words for each topic
   [top_words]
   type=pimlico.modules.gensim.lda_top_words
   input_model=lda
   num_words=10


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.gensim.lda_top_words`
    

