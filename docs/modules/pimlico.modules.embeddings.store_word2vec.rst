\!\! Store in word2vec format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_word2vec

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-------------------------------------------+
| Path       | pimlico.modules.embeddings.store_word2vec |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Takes embeddings stored in the default format used within Pimlico pipelines
(see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
using the ``word2vec`` storage format.

Uses the Gensim implementation of the storage, so depends on Gensim.


.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+------------+--------------------------------------+
| Name       | Type(s)                              |
+============+======================================+
| embeddings | **invalid input type specification** |
+------------+--------------------------------------+

Outputs
=======

+------------+---------------------------------------+
| Name       | Type(s)                               |
+============+=======================================+
| embeddings | **invalid output type specification** |
+------------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_store_word2vec_module]
   type=pimlico.modules.embeddings.store_word2vec
   input_embeddings=module_a.some_output
   

