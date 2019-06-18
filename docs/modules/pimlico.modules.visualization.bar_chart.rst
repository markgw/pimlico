\!\! Bar chart plotter
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.visualization.bar_chart

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------------------------+
| Path       | pimlico.modules.visualization.bar_chart |
+------------+-----------------------------------------+
| Executable | yes                                     |
+------------+-----------------------------------------+

Simple plotting of a bar chart from numeric data using Matplotlib

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| values | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| plot | **invalid output type specification** |
+------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_bar_chart_module]
   type=pimlico.modules.visualization.bar_chart
   input_values=module_a.some_output
   

