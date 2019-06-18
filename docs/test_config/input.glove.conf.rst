.. _test-config-glove.conf:

glove\_input\_test
~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=glove_input_test
   release=latest
   
   # Read in some vectors
   [vectors]
   type=pimlico.modules.input.embeddings.glove
   path=%(test_data_dir)s/input_data/glove/glove.small.300d.txt


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.input.embeddings.glove`
    

