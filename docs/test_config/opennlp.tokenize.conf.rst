.. _test-config-opennlp-tokenize.conf:

opennlp\_tokenize
~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=opennlp_tokenize
   release=latest
   
   # Prepared tarred corpus
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   # There's a problem with the tests here
   # Pimlico still has a clunky old Makefile-based system for installing model data for modules
   # The tests don't know that this needs to be done before the pipeline can be run
   # This is why this test is not in the main suite, but a special OpenNLP one
   [tokenize]
   type=pimlico.modules.opennlp.tokenize
   token_model=en-token.bin
   sentence_model=en-sent.bin


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.opennlp.tokenize`
    

