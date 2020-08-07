Store in word2vec format
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_word2vec

+------------+-------------------------------------------+
| Path       | pimlico.modules.embeddings.store_word2vec |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Takes embeddings stored in the default format used within Pimlico pipelines
(see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
using the ``word2vec`` storage format.

This is for using the vectors outside your pipeline, for example, for
distributing them publicly. For passing embeddings between Pimlico modules,
the internal :class:`~pimlico.datatypes.embeddings.Embeddings` datatype
should be used.

The output contains a ``bin`` file, containing the vectors in the binary
format, and a ``vocab`` file, containing the vocabulary and word counts.

Uses the Gensim implementation of the storage, so depends on Gensim.

Does not support Python 2, since we depend on Gensim.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+----------------------------------------------------------------------+
| Name       | Type(s)                                                              |
+============+======================================================================+
| embeddings | :class:`word2vec_files <pimlico.datatypes.embeddings.Word2VecFiles>` |
+------------+----------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_store_word2vec_module]
   type=pimlico.modules.embeddings.store_word2vec
   input_embeddings=module_a.some_output
   

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-embeddings-store_word2vec.conf`

