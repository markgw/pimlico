.. _test-config-europarl.conf:

europarl
~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=europarl
   release=latest
   
   # Read in some Europarl raw files, using the special Europarl reader
   [europarl]
   type=pimlico.modules.input.text.europarl
   files=%(test_data_dir)s/datasets/europarl_en_raw/*
   
   [store]
   type=pimlico.modules.corpora.store


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.store`
    

