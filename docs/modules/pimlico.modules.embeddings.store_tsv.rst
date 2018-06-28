Store in TSV format
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_tsv

+------------+--------------------------------------+
| Path       | pimlico.modules.embeddings.store_tsv |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Takes embeddings stored in the default format used within Pimlico pipelines
(see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
as TSV files.

These are suitable as input to the [Tensorflow Projector](https://projector.tensorflow.org/).


Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`Embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+-----------------------------------------------------------------+
| Name       | Type(s)                                                         |
+============+=================================================================+
| embeddings | :class:`~pimlico.modules.embeddings.store_tsv.info.TSVVecFiles` |
+------------+-----------------------------------------------------------------+

