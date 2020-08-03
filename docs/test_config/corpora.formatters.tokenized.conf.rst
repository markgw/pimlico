.. _test-config-corpora-formatters-tokenized.conf:

tokenized\_formatter
~~~~~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Test the tokenized text formatter
   [pipeline]
   name=tokenized_formatter
   release=latest
   
   # Take input from a prepared tokenized dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   # Format the tokenized data using the default formatter,
   # which is declared for the tokenized datatype
   [format]
   type=pimlico.modules.corpora.format


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.corpora.format`
    

