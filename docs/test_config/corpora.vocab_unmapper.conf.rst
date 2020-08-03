.. _test-config-corpora-vocab_unmapper.conf:

vocab\_unmapper
~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=vocab_unmapper
   release=latest
   
   # Load the prepared vocabulary
   #  (created by the vocab_builder test pipeline)
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab
   
   # Load the prepared word IDs
   [ids]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=IntegerListsDocumentType
   dir=%(test_data_dir)s/datasets/corpora/ids
   
   # Perform the mapping from IDs to words
   [tokens]
   type=pimlico.modules.corpora.vocab_unmapper
   input_vocab=vocab
   input_ids=ids
   oov=OOV


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.vocab_unmapper`
    

