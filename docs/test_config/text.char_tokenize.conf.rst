.. _test-config-text-char_tokenize.conf:

simple\_tokenize
~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=simple_tokenize
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   # This corpus is actually tokenized text, but we treat it as raw text and apply the char tokenizer
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   [tokenize]
   type=pimlico.modules.text.char_tokenize


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.text.char_tokenize`
    

