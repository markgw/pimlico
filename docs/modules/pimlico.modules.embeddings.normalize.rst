Normalize embeddings
~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.normalize

+------------+--------------------------------------+
| Path       | pimlico.modules.embeddings.normalize |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Apply normalization to a set of word embeddings.

For now, only one type of normalization is provided: L2 normalization.
Each vector is scaled so that its Euclidean magnitude is 1.

Other normalizations (like L1 or variance normalization) may be added in future.


Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+


Options
=======

+---------+------------------------------------------------------------------------+------+
| Name    | Description                                                            | Type |
+=========+========================================================================+======+
| l2_norm | Apply L2 normalization to scale each vector to unit length. Default: T | bool |
+---------+------------------------------------------------------------------------+------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_normalize_embeddings_module]
   type=pimlico.modules.embeddings.normalize
   input_embeddings=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_normalize_embeddings_module]
   type=pimlico.modules.embeddings.normalize
   input_embeddings=module_a.some_output
   l2_norm=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-normalize.conf`