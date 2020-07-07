Word2vec embedding reader \(Gensim\)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.word2vec

+------------+-------------------------------------------+
| Path       | pimlico.modules.input.embeddings.word2vec |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Reads in embeddings from the `word2vec <https://code.google.com/archive/p/word2vec/>`_ format, storing
them in the format used internally in Pimlico for embeddings. We use Gensim's implementation
of the format reader, so the module depends on Gensim.

Can be used, for example, to read the pre-trained embeddings
`offered by Google <https://code.google.com/archive/p/word2vec/>`_.


Inputs
======

No inputs

Outputs
=======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+


Options
=======

+--------+-------------------------------------------------------------+--------+
| Name   | Description                                                 | Type   |
+========+=============================================================+========+
| binary | Assume input is in word2vec binary format. Default: True    | bool   |
+--------+-------------------------------------------------------------+--------+
| limit  | Limit to the first N vectors in the file. Default: no limit | int    |
+--------+-------------------------------------------------------------+--------+
| path   | (required) Path to the word2vec embedding file (.bin)       | string |
+--------+-------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_word2vec_embedding_reader_module]
   type=pimlico.modules.input.embeddings.word2vec
   path=value

This example usage includes more options.

.. code-block:: ini
   
   [my_word2vec_embedding_reader_module]
   type=pimlico.modules.input.embeddings.word2vec
   binary=T
   limit=0
   path=value

