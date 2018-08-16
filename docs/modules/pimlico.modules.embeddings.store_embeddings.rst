Store embeddings (internal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_embeddings

+------------+---------------------------------------------+
| Path       | pimlico.modules.embeddings.store_embeddings |
+------------+---------------------------------------------+
| Executable | yes                                         |
+------------+---------------------------------------------+

Simply stores embeddings in the Pimlico internal format.

This is not often needed, but can be useful if reading embeddings for an
input reader that is slower than reading from the internal format. Then
you can use this module to do the reading and store the result before
passing it to other modules.


Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+----------------------------------------------------------------+
| Name       | Type(s)                                                        |
+============+================================================================+
| embeddings | :class:`~pimlico.datatypes.embeddings.Embeddings <embeddings>` |
+------------+----------------------------------------------------------------+

