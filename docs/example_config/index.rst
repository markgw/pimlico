.. _example-pipelines:

Example pipelines
~~~~~~~~~~~~~~~~~

Pimlico comes with a number of example pipelines to demonstrate how to 
use it. 

A more extensive set of examples is also provided in the form of 
:ref:`test pipelines <test-pipelines>`, which give a small example of the 
usage of individual core modules and are used as unit tests for the modules.

Available pipelines
===================

.. toctree::
   :maxdepth: 2
   :titlesonly:

   empty.rst
   simple.custom_module.rst
   simple.tokenize.rst


Running
=======

To run example pipelines, you can use the script ``run_example.sh`` in Pimlico's 
``example`` directory, e.g.:

.. code-block:: sh
   
   ./example_pipeline.sh simple/tokenize.conf status

This will load a single example pipeline from the given config file and show the 
execution status of the modules.

