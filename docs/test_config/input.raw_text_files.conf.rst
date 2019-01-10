.. _test-config-raw_text_files.conf:

raw\_text\_files\_test
~~~~~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=raw_text_files_test
   release=latest
   
   # Read in some Europarl raw files
   [europarl]
   type=pimlico.modules.input.text.raw_text_files
   files=%(test_data_dir)s/datasets/europarl_en_raw/*




