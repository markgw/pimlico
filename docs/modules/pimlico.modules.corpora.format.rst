Human-readable formatting
~~~~~~~~~~~~~~~~~~~~~~~~~

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

+--------+------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                  |
+========+==========================================================================================+
| corpus | :class:`grouped_corpus<DataPointType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+-------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                         |
+===========+=================================================================================================+
| formatted | :class:`~pimlico.datatypes.corpora.grouped.GroupedCorpus <grouped_corpus<RawTextDocumentType>>` |
+-----------+-------------------------------------------------------------------------------------------------+

Options
=======

+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name      | Description                                                                                                                                                                                                                                   | Type   |
+===========+===============================================================================================================================================================================================================================================+========+
| formatter | Fully qualified class name of a formatter to use to format the data. If not specified, the default formatter is used, which uses the datatype's browser_display attribute if available, or falls back to just converting documents to unicode | string |
+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

