\!\! OpenNLP coreference resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.coreference_pipeline

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+----------------------------------------------+
| Path       | pimlico.modules.opennlp.coreference_pipeline |
+------------+----------------------------------------------+
| Executable | yes                                          |
+------------+----------------------------------------------+

Runs the full coreference resolution pipeline using OpenNLP. This includes sentence splitting, tokenization,
pos tagging, parsing and coreference resolution. The results of all the stages are available in the output.

.. todo::

   Update to new datatypes system and add test pipeline

Use local config setting opennlp_memory to set the limit on Java heap memory for the OpenNLP processes. If
parallelizing, this limit is shared between the processes. That is, each OpenNLP worker will have a memory
limit of `opennlp_memory / processes`. That setting can use `g`, `G`, `m`, `M`, `k` and `K`, as in the Java setting.


Inputs
======

+------+--------------------------------------+
| Name | Type(s)                              |
+======+======================================+
| text | **invalid input type specification** |
+------+--------------------------------------+

Outputs
=======

+-------+---------------------------------------+
| Name  | Type(s)                               |
+=======+=======================================+
| coref | **invalid output type specification** |
+-------+---------------------------------------+


Optional
--------

+-----------+---------------------------------------+
| Name      | Type(s)                               |
+===========+=======================================+
| tokenized | **invalid output type specification** |
+-----------+---------------------------------------+
| pos       | **invalid output type specification** |
+-----------+---------------------------------------+
| parse     | **invalid output type specification** |
+-----------+---------------------------------------+

Options
=======

+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name           | Description                                                                                                                                                                                                               | Type   |
+================+===========================================================================================================================================================================================================================+========+
| gzip           | If True, each output, except annotations, for each document is gzipped. This can help reduce the storage occupied by e.g. parser or coref output. Default: False                                                          | bool   |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| token_model    | Tokenization model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)                                                                 | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| parse_model    | Parser model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/)                                                                                  | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| timeout        | Timeout in seconds for each individual coref resolution task. If this is exceeded, an InvalidDocument is returned for that document                                                                                       | int    |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| coref_model    | Coreference resolution model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in models/opennlp/) | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| readable       | If True, pretty-print the JSON output, so it's human-readable. Default: False                                                                                                                                             | bool   |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| pos_model      | POS tagger model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/)                                                                                    | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| sentence_model | Sentence segmentation model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)                                                        | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_opennlp_coref_module]
   type=pimlico.modules.opennlp.coreference_pipeline
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_opennlp_coref_module]
   type=pimlico.modules.opennlp.coreference_pipeline
   input_text=module_a.some_output
   gzip=T
   token_model=en-token.bin
   parse_model=en-parser-chunking.bin
   timeout=0
   coref_model=
   readable=T
   pos_model=en-pos-maxent.bin
   sentence_model=en-sent.bin

