.. _test-config-corpora-shuffle_linear.conf:

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
   
   # Read in some Europarl raw files
   # Instead of using the pre-prepared corpus stored in the pipeline-internal format,
   #  we use an input reader here. This means it wouldn't be possible to use
   #  the shuffle module type, so we're forced to use shuffle_linear.
   # Another solution is to use a store module and then shuffle, which may be preferable
   [europarl]
   type=pimlico.modules.input.text.raw_text_files
   files=%(test_data_dir)s/datasets/europarl_en_raw/*
   
   
   [shuffle]
   type=pimlico.modules.corpora.shuffle_linear


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.shuffle_linear`
    

