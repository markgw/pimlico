R script executor
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.r.script

+------------+--------------------------+
| Path       | pimlico.modules.r.script |
+------------+--------------------------+
| Executable | yes                      |
+------------+--------------------------+

Simple interface to R that just involves running a given R script, first substituting in some paths from the
pipeline, making it easy to pass in data from the output of other modules.


Inputs
======

+---------+---------------------------------------------------------------------------+
| Name    | Type(s)                                                                   |
+=========+===========================================================================+
| sources | list of :class:`PimlicoDatatype <pimlico.datatypes.base.PimlicoDatatype>` |
+---------+---------------------------------------------------------------------------+

Outputs
=======

+--------+--------------------------------------------+
| Name   | Type(s)                                    |
+========+============================================+
| output | :func:`~pimlico.datatypes.files.NamedFile` |
+--------+--------------------------------------------+

Options
=======

+--------+-------------+--------+
| Name   | Description | Type   |
+========+=============+========+
| script | (required)  | string |
+--------+-------------+--------+

