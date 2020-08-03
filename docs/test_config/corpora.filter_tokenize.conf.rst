.. _test-config-corpora-filter_tokenize.conf:

filter\_tokenize
~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Essentially the same as the simple_tokenize test pipeline,
   # but uses the filter=T parameter on the tokenizer.
   # This can be applied to any document map module, so this
   # is intended as a test for that feature, rather than for
   # simple_tokenize
   
   [pipeline]
   name=filter_tokenize
   release=latest
   
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   # This corpus is actually tokenized text, but we treat it as raw text and apply the simple tokenizer
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   # Tokenize as a filter: this module is not executable
   [tokenize]
   type=pimlico.modules.text.simple_tokenize
   filter=T
   
   # Then store the output
   # You wouldn't really want to do this, as it's equivalent to not using
   # the tokenizer as a filter! But we're testing the filter feature
   [store]
   type=pimlico.modules.corpora.store
   


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.store`
    

