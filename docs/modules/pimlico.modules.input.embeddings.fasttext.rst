FastText embedding reader \(bin\)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.embeddings.fasttext

+------------+-------------------------------------------+
| Path       | pimlico.modules.input.embeddings.fasttext |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Reads in embeddings from the `FastText <https://github.com/facebookresearch/fastText>`_ format, storing
them in the format used internally in Pimlico for embeddings.

Loads the fastText ``.bin`` format using the fasttext library itself. Outputs
both a fixed set of embeddings in Pimlico's standard format and a special
fastText datatype that provides access to more features of the model.


Inputs
======

No inputs

Outputs
=======

+------------+--------------------------------------------------------------------------------+
| Name       | Type(s)                                                                        |
+============+================================================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>`                  |
+------------+--------------------------------------------------------------------------------+
| model      | :class:`fasttext_embeddings <pimlico.datatypes.embeddings.FastTextEmbeddings>` |
+------------+--------------------------------------------------------------------------------+


Options
=======

+------+------------------------------------------------+--------+
| Name | Description                                    | Type   |
+======+================================================+========+
| path | (required) Path to the FastText embedding file | string |
+------+------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fasttext_bin_embedding_reader_module]
   type=pimlico.modules.input.embeddings.fasttext
   path=value

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-input-fasttext.conf`

