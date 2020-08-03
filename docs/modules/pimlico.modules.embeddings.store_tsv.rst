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

This is for using the vectors outside your pipeline, for example, for
distributing them publicly or using as input to an external visualization
tool. For passing embeddings between Pimlico modules,
the internal :class:`~pimlico.datatypes.embeddings.Embeddings` datatype
should be used.

These are suitable as input to the `Tensorflow Projector <https://projector.tensorflow.org/>`_.


Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+-------------------------------------------------------------------+
| Name       | Type(s)                                                           |
+============+===================================================================+
| embeddings | :class:`tsv_vec_files <pimlico.datatypes.embeddings.TSVVecFiles>` |
+------------+-------------------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_store_tsv_module]
   type=pimlico.modules.embeddings.store_tsv
   input_embeddings=module_a.some_output
   

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-embeddings-store_tsv.conf`

