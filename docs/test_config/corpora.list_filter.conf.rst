.. _test-config-list_filter.conf:

list_filter
~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   [pipeline]
   name=list_filter
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=RawTextDocumentType
   dir=%(test_data_dir)s/datasets/text_corpora/europarl
   
   [filename_list]
   type=StringList
   dir=%(test_data_dir)s/datasets/europarl_filename_list
   
   # Use the filename list to filter the documents
   # This should leave 3 documents (of original 5)
   [europarl_filtered]
   type=pimlico.modules.corpora.list_filter
   input_corpus=europarl
   input_list=filename_list


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.list_filter`
    

