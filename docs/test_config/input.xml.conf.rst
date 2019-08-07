.. _test-config-xml.conf:

xml\_test
~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Test for the XML input module
   #
   # Read in raw text data from the Estonian Reference Corpus:
   # https://www.cl.ut.ee/korpused/segakorpus/
   # We have a tiny subset of the corpus here. It can be read using
   # the standard XML input module.
   
   [pipeline]
   name=xml_test
   release=latest
   
   # Read in some XML files from Est Ref
   [input]
   type=pimlico.modules.input.xml
   files=%(test_data_dir)s/datasets/est_ref/*.tei
   document_node_type=text




