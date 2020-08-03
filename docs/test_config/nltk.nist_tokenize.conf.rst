.. _test-config-nltk-nist_tokenize.conf:

nltk\_nist\_tokenize
~~~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=nltk_nist_tokenize
   release=latest
   
   # Prepared grouped corpus of raw text data
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   # Tokenize the data using NLTK's simple NIST tokenizer
   [tokenize_euro]
   type=pimlico.modules.nltk.nist_tokenize
   
   # Another tokenization, using the non_european option
   [tokenize_non_euro]
   type=pimlico.modules.nltk.nist_tokenize
   input=europarl
   non_european=T


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.nltk.nist_tokenize`
 * :mod:`pimlico.modules.nltk.nist_tokenize`
    

