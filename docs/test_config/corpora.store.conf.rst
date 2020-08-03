.. _test-config-corpora-store.conf:

store
~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=store
   release=latest
   
   # Read in some Europarl raw files
   [europarl]
   type=pimlico.modules.input.text.raw_text_files
   files=%(test_data_dir)s/datasets/europarl_en_raw/*
   encoding=utf8
   
   # Group works as a filter module, so its output is not stored.
   # This pipeline shows how you can store the output from such a
   #  module for static use by later modules.
   # In this exact case, you don't gain anything by doing that, since
   # the grouping filter is fast, but sometimes it could be desirable
   # with other filters
   [group]
   type=pimlico.modules.corpora.group
   
   [store]
   type=pimlico.modules.corpora.store


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.group`
 * :mod:`pimlico.modules.corpora.store`
    

