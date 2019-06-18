\!\! OpenNLP NER
~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.ner

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------------+
| Path       | pimlico.modules.opennlp.ner |
+------------+-----------------------------+
| Executable | yes                         |
+------------+-----------------------------+

Named-entity recognition using OpenNLP's tools.

By default, uses the pre-trained English model distributed with OpenNLP. If you want to use other models (e.g.
for other languages), download them from the OpenNLP website to the models dir (`models/opennlp`) and specify
the model name as an option.

Note that the default model is for identifying person names only. You can identify other name types by loading
other pre-trained OpenNLP NER models. Identification of multiple name types at the same time is not (yet)
implemented.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+------+--------------------------------------+
| Name | Type(s)                              |
+======+======================================+
| text | **invalid input type specification** |
+------+--------------------------------------+

Outputs
=======

+-----------+---------------------------------------+
| Name      | Type(s)                               |
+===========+=======================================+
| documents | **invalid output type specification** |
+-----------+---------------------------------------+

Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                     | Type   |
+=======+=================================================================================================================================+========+
| model | NER model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/) | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_opennlp_ner_module]
   type=pimlico.modules.opennlp.ner
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_opennlp_ner_module]
   type=pimlico.modules.opennlp.ner
   input_text=module_a.some_output
   model=en-ner-person.bin

