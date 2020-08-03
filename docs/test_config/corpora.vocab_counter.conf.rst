.. _test-config-corpora-vocab_counter.conf:

vocab\_counter
~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=vocab_counter
   release=latest
   
   # Load the prepared vocabulary
   #  (created by the vocab_builder test pipeline)
   [vocab]
   type=pimlico.datatypes.dictionary.Dictionary
   dir=%(test_data_dir)s/datasets/vocab
   
   # Load the prepared token IDs
   #  (created by the vocab_mapper test pipeline)
   [ids]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=IntegerListsDocumentType
   dir=%(test_data_dir)s/datasets/corpora/ids
   
   # Count the frequency of each word in the corpus
   [counts]
   type=pimlico.modules.corpora.vocab_counter
   input_corpus=ids
   input_vocab=vocab


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.vocab_counter`
    

