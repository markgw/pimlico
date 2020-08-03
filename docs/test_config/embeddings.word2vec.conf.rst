.. _test-config-embeddings-word2vec.conf:

word2vec\_train
~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=word2vec_train
   release=latest
   
   # Take tokenized text input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   [word2vec]
   type=pimlico.modules.embeddings.word2vec
   # Set low, since we're training on a tiny corpus
   min_count=1
   # Very small vectors: usually this will be more like 100 or 200
   size=10


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.embeddings.word2vec`
    

