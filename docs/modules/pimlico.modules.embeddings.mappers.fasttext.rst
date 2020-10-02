fastText to doc\-embedding mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.mappers.fasttext

+------------+---------------------------------------------+
| Path       | pimlico.modules.embeddings.mappers.fasttext |
+------------+---------------------------------------------+
| Executable | yes                                         |
+------------+---------------------------------------------+

Use trained fastText embeddings to map words to their embeddings,
including OOVs, using sub-word information.

First train a fastText model using the fastText training module. Then
use this module to produce a doc-embeddings mapper.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------------+--------------------------------------------------------------------------------+
| Name       | Type(s)                                                                        |
+============+================================================================================+
| embeddings | :class:`fasttext_embeddings <pimlico.datatypes.embeddings.FastTextEmbeddings>` |
+------------+--------------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                  |
+========+==========================================================================================+
| mapper | :class:`fasttext_doc_embeddings_mapper <pimlico.datatypes.embeddings.FastTextDocMapper>` |
+--------+------------------------------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fasttext_doc_mapper_module]
   type=pimlico.modules.embeddings.mappers.fasttext
   input_embeddings=module_a.some_output
   

