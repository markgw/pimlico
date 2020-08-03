.. _test-config-text-normalize.conf:

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
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   [norm]
   type=pimlico.modules.text.normalize
   case=lower
   remove_empty=T


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.text.normalize`
    

