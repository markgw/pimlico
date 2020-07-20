.. _test-config-core-filter_map.conf:

filter\_map
~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Pipeline designed to test the use of a document
   # map module as a filter. It uses the text normalization
   # module and will therefore fail if that module's
   # test is also failing, but since the module is so
   # simple, this is unlikely
   
   [pipeline]
   name=filter_map
   release=latest
   
   # Take input from a prepared Pimlico dataset
   [europarl]
   type=pimlico.datatypes.corpora.GroupedCorpus
   data_point_type=TokenizedDocumentType
   dir=%(test_data_dir)s/datasets/corpora/tokenized
   
   # Apply text normalization
   # Unlike the test text/normalize.conf, we apply this
   # as a filter, so its result is not stored, but computed
   # on the fly and passed straight through to the
   # next module
   [norm_filter]
   type=pimlico.modules.text.normalize
   # Use the general filter option, which can be applied
   # to any document map module
   filter=T
   case=lower
   
   # Store the result of the previous, filter, module.
   # This is a stupid thing to do, since we could have
   # just not used the module as a filter and had the
   # same effect, but we do it here to test the use
   # of a module as a filter
   [store]
   type=pimlico.modules.corpora.store


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.corpora.store`
    

