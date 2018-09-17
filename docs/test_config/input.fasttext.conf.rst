.. _test-config-fasttext.conf:

fasttext_input_test
~~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=fasttext_input_test
   release=latest
   
   # Read in some vectors
   [vectors]
   type=pimlico.modules.input.embeddings.fasttext
   path=%(test_data_dir)s/input_data/fasttext/wiki.en_top50.vec


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.input.embeddings.fasttext`
    

