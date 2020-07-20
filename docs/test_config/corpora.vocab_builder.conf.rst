.. _test-config-corpora-vocab_builder.conf:

vocab\_builder
~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=vocab_builder
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   [vocab]
   type=pimlico.modules.corpora.vocab_builder
   threshold=2
   limit=500


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.vocab_builder`
    

