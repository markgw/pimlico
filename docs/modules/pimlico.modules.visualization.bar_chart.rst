Bar chart plotter
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.visualization.bar_chart

+------------+-----------------------------------------+
| Path       | pimlico.modules.visualization.bar_chart |
+------------+-----------------------------------------+
| Executable | yes                                     |
+------------+-----------------------------------------+

Simple plotting of a bar chart from numeric results data using Matplotlib.


Inputs
======

+---------+----------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                    |
+=========+============================================================================================================================+
| results | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`numeric_result <pimlico.datatypes.results.NumericResult>` |
+---------+----------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+------------------------------------------------------------------------+
| Name | Type(s)                                                                |
+======+========================================================================+
| plot | :class:`named_file_collection <pimlico.datatypes.plotting.PlotOutput>` |
+------+------------------------------------------------------------------------+


Options
=======

+--------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Name   | Description                                                                                                                                                                                                                                            | Type               |
+========+========================================================================================================================================================================================================================================================+====================+
| colors | Pyplot colors to use for each series. If shorter than the number of inputs, cycles round. Specify according to pyplot docs: https://matplotlib.org/2.0.2/api/colors_api.html. E.g. use single-letter color names, HTML color codes or HTML color names | absolute file path |
+--------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| labels | If given, a list of labels corresponding to the inputs to use in plots. Otherwise, inputs are numbered and the labels provided in their label fields are used                                                                                          | absolute file path |
+--------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_bar_chart_module]
   type=pimlico.modules.visualization.bar_chart
   input_results=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_bar_chart_module]
   type=pimlico.modules.visualization.bar_chart
   input_results=module_a.some_output
   colors=r,g,b,y,c,m,k
   labels=path1,path2,...

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-visualization-bar_chart.conf`

