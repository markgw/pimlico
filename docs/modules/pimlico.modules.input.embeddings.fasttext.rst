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

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+


Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                           | Type   |
+=======+=======================================================================================================================================+========+
| limit | Limit to the first N words. Since the files are typically ordered from most to least frequent, this limits to the N most common words | int    |
+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+
| path  | (required) Path to the FastText embedding file                                                                                        | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fasttext_embedding_reader_module]
   type=pimlico.modules.input.embeddings.fasttext
   path=value

This example usage includes more options.

.. code-block:: ini
   
   [my_fasttext_embedding_reader_module]
   type=pimlico.modules.input.embeddings.fasttext
   limit=0
   path=value

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-fasttext.conf`