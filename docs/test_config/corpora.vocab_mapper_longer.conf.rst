.. _test-config-corpora-vocab_mapper_longer.conf:

vocab\_mapper
~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=vocab_mapper
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized_longer
   
   # Load the prepared vocabulary
   #  (created by the vocab_builder test pipeline)
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab
   
   # Perform the mapping from words to IDs
   [ids]
   type=pimlico.modules.corpora.vocab_mapper
   input_vocab=vocab
   input_text=europarl


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.vocab_mapper`
    

