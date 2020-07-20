.. _test-config-corpora-group.conf:

group
~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=group
   release=latest
   
   # Read in some Europarl raw files
   [europarl]
   type=pimlico.modules.input.text.raw_text_files
   files=%(test_data_dir)s/datasets/europarl_en_raw/*
   encoding=utf8
   
   [group]
   type=pimlico.modules.corpora.group
   
   [output]
   type=pimlico.modules.corpora.format


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.group`
 * :mod:`~pimlico.modules.corpora.format`
    

