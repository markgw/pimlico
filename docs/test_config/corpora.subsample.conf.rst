.. _test-config-corpora-subsample.conf:

subsample
~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=subsample
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [subsample]
   type=pimlico.modules.corpora.subsample
   p=0.8
   seed=1


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.subsample`
    

