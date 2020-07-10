.. _test-config-normalize.conf:

embedding\_norm
~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Output trained embeddings in the word2vec format for external use
   [pipeline]
   name=embedding_norm
   release=latest
   
   # Take trained embeddings from a prepared Pimlico dataset
   [embeddings]
   type=pimlico.datatypes.embeddings.Embeddings
   dir=%(test_data_dir)s/datasets/embeddings
   
   # Apply L2 normalization: scale all vectors to unit length
   [norm]
   type=pimlico.modules.embeddings.normalize
   l2_norm=T


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.embeddings.normalize`
    

