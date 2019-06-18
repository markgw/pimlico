Human\-readable formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.format

+------------+--------------------------------+
| Path       | pimlico.modules.corpora.format |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Corpus formatter

Pimlico provides a data browser to make it easy to view documents in a tarred document corpus. Some datatypes
provide a way to format the data for display in the browser, whilst others provide multiple formatters that
display the data in different ways.

This module allows you to use this formatting functionality to output the formatted data as a corpus. Since the
formatting operations are designed for display, this is generally only useful to output the data for human
consumption.


Inputs
======

+--------+---------------------------------------------------------------------------+
| Name   | Type(s)                                                                   |
+========+===========================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+---------------------------------------------------------------------------+

Outputs
=======

+-----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                              |
+===========+======================================================================================================================================================================+
| formatted | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+-----------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Options
=======

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name      | Description                                                                                                                                                                                                                                   | Type   |
+===========+===============================================================================================================================================================================================================================================+========+
| formatter | Fully qualified class name of a formatter to use to format the data. If not specified, the default formatter is used, which uses the datatype's browser_display attribute if available, or falls back to just converting documents to unicode | string |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_format_module]
   type=pimlico.modules.corpora.format
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_format_module]
   type=pimlico.modules.corpora.format
   input_corpus=module_a.some_output
   formatter=path.to.formatter.FormatterClass

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-tokenized.conf`