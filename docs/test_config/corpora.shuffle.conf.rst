.. _test-config-corpora-shuffle.conf:

shuffle
~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=shuffle
   release=latest
   
   # Take input from a prepared Pimlico dataset
   # This works fine with shuffle, since it's already stored in the pipeline-internal format
   # However, it wouldn't work with an input reader, since
   #  the interface doesn't provide random access to docs
   # Then you'd need to use shuffle_linear
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [shuffle]
   type=pimlico.modules.corpora.shuffle


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.shuffle`
    

