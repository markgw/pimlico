.. _test-config-input-huggingface.conf:

huggingface\_dataset
~~~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=huggingface_dataset
   release=latest
   
   # Load an example dataset from Huggingface
   [hf_dataset]
   type=pimlico.modules.input.text.huggingface
   dataset=glue
   name=mrpc
   split=train
   doc_name=idx
   columns=sentence1,sentence2


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.input.text.huggingface`
    

