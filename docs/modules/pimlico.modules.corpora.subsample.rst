Random subsample
~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.subsample

+------------+-----------------------------------+
| Path       | pimlico.modules.corpora.subsample |
+------------+-----------------------------------+
| Executable | yes                               |
+------------+-----------------------------------+

Randomly subsample documents of a corpus at a given rate to create a smaller corpus.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+--------+---------------------------------------------------------------------------+
| Name   | Type(s)                                                                   |
+========+===========================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+---------------------------------------------------------------------------+

Outputs
=======

+--------+--------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                |
+========+========================================================================================================+
| corpus | :class:`corpus with data-point from input <pimlico.datatypes.corpora.grouped.CorpusWithTypeFromInput>` |
+--------+--------------------------------------------------------------------------------------------------------+


Options
=======

+--------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+
| Name         | Description                                                                                                                                                                                                                                                                                                      | Type  |
+==============+==================================================================================================================================================================================================================================================================================================================+=======+
| p            | (required) Probability of including any given document. The resulting corpus will be roughly this proportion of the size of the input. Alternatively, you can specify an integer, which will be interpreted as the target size of the output. A p value will be calculated based on the size of the input corpus | float |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+
| seed         | Random seed. We always set a random seed before starting to ensure some level of reproducability                                                                                                                                                                                                                 | int   |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+
| skip_invalid | Skip over any invalid documents so that the output subset contains just valid document and no invalid ones. By default, invalid documents are passed through                                                                                                                                                     | bool  |
+--------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_subsample_module]
   type=pimlico.modules.corpora.subsample
   input_corpus=module_a.some_output
   p=0.1

This example usage includes more options.

.. code-block:: ini
   
   [my_subsample_module]
   type=pimlico.modules.corpora.subsample
   input_corpus=module_a.some_output
   p=0.1
   seed=1234
   skip_invalid=T

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-corpora-subsample.conf`

