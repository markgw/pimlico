Pimlico module: CAEVO event extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.caevo

+------------+-----------------------+
| Path       | pimlico.modules.caevo |
+------------+-----------------------+
| Executable | yes                   |
+------------+-----------------------+

`CAEVO <http://www.usna.edu/Users/cs/nchamber/caevo/>`_ is Nate Chambers' CAscading EVent Ordering system,
a tool for extracting events of many types from text and ordering them.

`CAEVO is open source <https://github.com/nchambers/caevo>`_, implemented in Java, so is easily integrated
into Pimlico using Py4J.

.. todo::

   The implementation of this module is incomplete. I've mostly written the Py4J gateway, but not the Python side yet.


Inputs
======

+-----------+---------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                       |
+===========+===============================================================================================================+
| documents | :class:`CoNLLDependencyParseInputCorpus <pimlico.datatypes.parse.dependency.CoNLLDependencyParseInputCorpus>` |
+-----------+---------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+------------------------------------------------------------+
| Name   | Type(s)                                                    |
+========+============================================================+
| parsed | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+--------+------------------------------------------------------------+

Options
=======

+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name    | Description                                                                                                                                                                                              | Type   |
+=========+==========================================================================================================================================================================================================+========+
| model   | Filename of parsing model, or path to the file. If just a filename, assumed to be Malt models dir (models/malt). Default: engmalt.linear-1.7.mco, which can be acquired by 'make malt' in the models dir | string |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| no_gzip | By default, we gzip each document in the output data. If you don't do this, the output can get very large, since it's quite a verbose output format                                                      | bool   |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

