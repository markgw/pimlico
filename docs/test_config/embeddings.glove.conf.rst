.. _test-config-embeddings-glove.conf:

glove\_train
~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Train GloVe embeddings on a tiny corpus
   [pipeline]
   name=glove_train
   release=latest
   
   # Take tokenized text input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   [glove]
   type=pimlico.modules.embeddings.glove
   # Set low, since we're training on a tiny corpus
   min_count=1
   # TODO Set more options


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.embeddings.glove`
    

