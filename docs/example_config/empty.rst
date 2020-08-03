.. _example-pipeline-empty-test:

empty\_test
~~~~~~~~~~~



This is an example Pimlico pipeline.

The complete config file for this example pipeline is below. `Source file <https://github.com/markgw/pimlico/blob/master/examples/empty.conf>`_

A basic, empty pipeline.
Includes no modules at all.

Used to test basic loading of pipelines in one of the unit tests.

Pipeline config
===============

.. code-block:: ini
   
   [pipeline]
   name=empty_test
   # Always test with the latest version
   release=latest
   
   [vars]
   var_name=testing a variable



