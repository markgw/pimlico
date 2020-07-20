.. _test-config-embeddings-store_tsv.conf:

tsvvec\_store
~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Output trained embeddings in the TSV format for external use
   [pipeline]
   name=tsvvec_store
   release=latest
   
   # Take trained embeddings from a prepared Pimlico dataset
   [embeddings]
   type=pimlico.datatypes.embeddings.Embeddings
   dir=%(test_data_dir)s/datasets/embeddings
   
   [store]
   type=pimlico.modules.embeddings.store_tsv


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.embeddings.store_tsv`
    

