.. _test-config-text_normalize.conf:

normalize
~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=normalize
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [norm]
   type=pimlico.modules.text.text_normalize
   case=lower
   strip=T
   blank_lines=T


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.text.text_normalize`
    

