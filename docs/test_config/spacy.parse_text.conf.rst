.. _test-config-spacy-parse_text.conf:

spacy\_parse\_text
~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=spacy_parse_text
   release=latest
   
   # Prepared tarred corpus
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [tokenize]
   type=pimlico.modules.spacy.parse_text
   model=en_core_web_sm


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.spacy.parse_text`
    

