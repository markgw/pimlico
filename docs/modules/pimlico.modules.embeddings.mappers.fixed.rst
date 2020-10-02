Fixed embeddings to doc\-embedding mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.mappers.fixed

+------------+------------------------------------------+
| Path       | pimlico.modules.embeddings.mappers.fixed |
+------------+------------------------------------------+
| Executable | yes                                      |
+------------+------------------------------------------+

Use trained fixed word embeddings to map words to their embeddings.
Does nothing with OOVs, which we don't have any way to map.

First train or load embeddings using another module.
Then use this module to produce a doc-embeddings mapper.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+--------+---------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                 |
+========+=========================================================================================================+
| mapper | :class:`fixed_embeddings_doc_embeddings_mapper <pimlico.datatypes.embeddings.FixedEmbeddingsDocMapper>` |
+--------+---------------------------------------------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_fixed_embeddings_doc_mapper_module]
   type=pimlico.modules.embeddings.mappers.fixed
   input_embeddings=module_a.some_output
   

