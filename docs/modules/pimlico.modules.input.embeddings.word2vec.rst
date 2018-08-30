Word2vec embedding reader (Gensim)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

+--------+----------------------------------------------------------+--------+
| Name   | Description                                              | Type   |
+========+==========================================================+========+
| binary | Assume input is in word2vec binary format. Default: True | bool   |
+--------+----------------------------------------------------------+--------+
| path   | (required) Path to the word2vec embedding file (.bin)    | string |
+--------+----------------------------------------------------------+--------+

