.. _test-config-opennlp-parse.conf:

opennlp\_parse
~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # The input data from Europarl has very long sentences, which makes the parser slow.
   # It would be better to run the tests on input that would not take so long
   [pipeline]
   name=opennlp_parse
   release=latest
   
   # Prepared tarred corpus
   [tokens]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   # There's a problem with the tests here
   # Pimlico still has a clunky old Makefile-based system for installing model data for modules
   # The tests don't know that this needs to be done before the pipeline can be run
   # This is why this test is not in the main suite, but a special OpenNLP one
   [parse]
   type=pimlico.modules.opennlp.parse
   model=en-parser-chunking.bin


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.opennlp.parse`
    

