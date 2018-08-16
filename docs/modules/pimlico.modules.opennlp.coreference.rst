!! OpenNLP coreference resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.coreference

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-------------------------------------+
| Path       | pimlico.modules.opennlp.coreference |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline

Use local config setting opennlp_memory to set the limit on Java heap memory for the OpenNLP processes. If
parallelizing, this limit is shared between the processes. That is, each OpenNLP worker will have a memory
limit of `opennlp_memory / processes`. That setting can use `g`, `G`, `m`, `M`, `k` and `K`, as in the Java setting.


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| parses | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+-------+---------------------------------------+
| Name  | Type(s)                               |
+=======+=======================================+
| coref | **invalid output type specification** |
+-------+---------------------------------------+

Options
=======

+----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name     | Description                                                                                                                                                                                                               | Type   |
+==========+===========================================================================================================================================================================================================================+========+
| gzip     | If True, each output, except annotations, for each document is gzipped. This can help reduce the storage occupied by e.g. parser or coref output. Default: False                                                          | bool   |
+----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| model    | Coreference resolution model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in models/opennlp/) | string |
+----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| readable | If True, pretty-print the JSON output, so it's human-readable. Default: False                                                                                                                                             | bool   |
+----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| timeout  | Timeout in seconds for each individual coref resolution task. If this is exceeded, an InvalidDocument is returned for that document                                                                                       | int    |
+----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

