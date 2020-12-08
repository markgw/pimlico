.. _test-config-visualization-bar_chart.conf:

bar\_chart
~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Plot several numbers on a bar chart
   [pipeline]
   name=bar_chart
   release=latest
   
   [a]
   type=NumericResult
   dir=%(test_data_dir)s/datasets/results/A
   
   [b]
   type=NumericResult
   dir=%(test_data_dir)s/datasets/results/C
   
   [c]
   type=NumericResult
   dir=%(test_data_dir)s/datasets/results/C
   
   [plot]
   type=pimlico.modules.visualization.bar_chart
   input=a,b,c


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`pimlico.modules.visualization.bar_chart`
    

