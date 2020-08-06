FastText embedding reader \(Gensim\)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.fasttext_gensim

+------------+--------------------------------------------------+
| Path       | pimlico.modules.input.embeddings.fasttext_gensim |
+------------+--------------------------------------------------+
| Executable | yes                                              |
+------------+--------------------------------------------------+

Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
them in the format used internally in Pimlico for embeddings. This version uses Gensim's implementation
of the format reader, so depends on Gensim.

Can be used, for example, to read the
`pre-trained embeddings <https://github.com/facebookresearch/fastText/blob/master/pretrained-vectors.md>`_
offered by Facebook AI.

Reads only the binary format (``.bin``), not the text format (``.vec``).

Does not support Python 2, since Gensim has dropped Python 2 support.

.. seealso::

   :mod:`pimlico.modules.input.embeddings.fasttext`:
      An alternative reader that does not use Gensim. It permits (only) reading the text format.

.. todo::

   Add test pipeline. This is slightly difficult, as we need a small FastText binary
   file, which is harder to produce, since you can't easily just truncate a big file.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

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

+------+-------------------------------------------------------+--------+
| Name | Description                                           | Type   |
+======+=======================================================+========+
| path | (required) Path to the FastText embedding file (.bin) | string |
+------+-------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fasttext_embedding_reader_gensim_module]
   type=pimlico.modules.input.embeddings.fasttext_gensim
   path=value

