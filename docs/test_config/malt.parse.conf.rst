.. _test-config-malt-parse.conf:

malt\_parse
~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # The input data from Europarl has very long sentences, which makes the parser slow.
   # It would be better to run the tests on input that would not take so long
   [pipeline]
   name=malt_parse
   release=latest
   
   # Load pre-tagged data
   # This is in word-annotation format and was produced by the OpenNLP tagger test pipeline
   [pos]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=WordAnnotationsDocumentType(fields=word,pos)
   dir=%(test_data_dir)s/datasets/corpora/pos
   
   [parse]
   type=pimlico.modules.malt


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.malt`
    

