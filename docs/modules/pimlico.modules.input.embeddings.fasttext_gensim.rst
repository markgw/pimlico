!! FastText embedding reader using Gensim
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.fasttext_gensim

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

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

.. seealso::

   :mod:`pimlico.modules.input.embeddings.fasttext`:
      An alternative reader that does not use Gensim. It permits (only) reading the text format.

.. todo::

   Add test pipeline. This is slightly difficult, as we need a small FastText binary
   file, which is harder to produce, since you can't easily just truncate a big file.


Inputs
======

No inputs

Outputs
=======

+------------+----------------------------------------------------------------+
| Name       | Type(s)                                                        |
+============+================================================================+
| embeddings | :class:`~pimlico.datatypes.embeddings.Embeddings <embeddings>` |
+------------+----------------------------------------------------------------+

Options
=======

+------+-------------------------------------------------------+--------+
| Name | Description                                           | Type   |
+======+=======================================================+========+
| path | (required) Path to the FastText embedding file (.bin) | string |
+------+-------------------------------------------------------+--------+

