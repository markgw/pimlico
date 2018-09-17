.. _test-config-interleave.conf:

interleave
~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=interleave
   release=latest
   
   # Take input from some prepared Pimlico datasets
   [europarl1]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [europarl2]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl2
   
   
   [interleave]
   type=pimlico.modules.corpora.interleave
   input_corpora=europarl1,europarl2
   
   [output]
   type=pimlico.modules.corpora.format


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.interleave`
 * :mod:`~pimlico.modules.corpora.format`
    

