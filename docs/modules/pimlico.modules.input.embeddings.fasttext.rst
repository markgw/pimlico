FastText embedding reader
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.fasttext

+------------+-------------------------------------------+
| Path       | pimlico.modules.input.embeddings.fasttext |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
them in the format used internally in Pimlico for embeddings.

Can be used, for example, to read the
`pre-trained embeddings <https://github.com/facebookresearch/fastText/blob/master/pretrained-vectors.md>`_
offered by Facebook AI.

Currently only reads the text format (``.vec``), not the binary format (``.bin``).

.. seealso::

   :mod:`pimlico.modules.input.embeddings.fasttext_gensim`:
      An alternative reader that uses Gensim's FastText format reading code and permits reading from the
      binary format, which contains more information.


Inputs
======

No inputs

Outputs
=======

+------------+---------------------------------------------------+
| Name       | Type(s)                                           |
+============+===================================================+
| embeddings | :class:`~pimlico.datatypes.embeddings.Embeddings` |
+------------+---------------------------------------------------+

Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                           | Type   |
+=======+=======================================================================================================================================+========+
| path  | (required) Path to the FastText embedding file                                                                                        | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+
| limit | Limit to the first N words. Since the files are typically ordered from most to least frequent, this limits to the N most common words | int    |
+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+
