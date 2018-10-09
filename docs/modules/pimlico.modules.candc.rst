!! C&C parser
~~~~~~~~~~~~~

.. py:module:: pimlico.modules.candc

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------+
| Path       | pimlico.modules.candc |
+------------+-----------------------+
| Executable | yes                   |
+------------+-----------------------+

Wrapper around the original `C&C parser <http://svn.ask.it.usyd.edu.au/trac/candc/>`_.

Takes tokenized input and parses it with C&C. The output is written exactly as it comes out from C&C.
It contains both GRs and supertags, plus POS-tags, etc.

The wrapper uses C&C's SOAP server. It sets the SOAP server running in the background and then calls C&C's
SOAP client for each document. If parallelizing, multiple SOAP servers are set going and each one is kept
constantly fed with documents.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-----------+--------------------------------------+
| Name      | Type(s)                              |
+===========+======================================+
| documents | **invalid input type specification** |
+-----------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| parsed | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                                                                                                         | Type   |
+=======+=====================================================================================================================================================================================================================+========+
| model | Absolute path to models directory or name of model set. If not an absolute path, assumed to be a subdirectory of the candcs models dir (see instructions in models/candc/README on how to fetch pre-trained models) | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_candc_module]
   type=pimlico.modules.candc
   input_documents=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_candc_module]
   type=pimlico.modules.candc
   input_documents=module_a.some_output
   model=ccgbank

