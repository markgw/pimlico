!! Store in TSV format
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_tsv

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+--------------------------------------+
| Path       | pimlico.modules.embeddings.store_tsv |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Takes embeddings stored in the default format used within Pimlico pipelines
(see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
as TSV files.

These are suitable as input to the [Tensorflow Projector](https://projector.tensorflow.org/).

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+------------+--------------------------------------+
| Name       | Type(s)                              |
+============+======================================+
| embeddings | **invalid input type specification** |
+------------+--------------------------------------+

Outputs
=======

+------------+---------------------------------------+
| Name       | Type(s)                               |
+============+=======================================+
| embeddings | **invalid output type specification** |
+------------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_store_tsv_module]
   input_embeddings=module_a.some_output
   

