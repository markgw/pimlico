CAEVO event extractor
~~~~~~~~~~~~~~~~~~~~~

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


Inputs
======

+-----------+------------------------------------------------------------+
| Name      | Type(s)                                                    |
+===========+============================================================+
| documents | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+-----------+------------------------------------------------------------+

Outputs
=======

+--------+-----------------------------------------------+
| Name   | Type(s)                                       |
+========+===============================================+
| events | :class:`~pimlico.datatypes.caevo.CaevoCorpus` |
+--------+-----------------------------------------------+

Options
=======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name   | Description                                                                                                                                                          | Type   |
+========+======================================================================================================================================================================+========+
| sieves | Filename of sieve list file, or path to the file. If just a filename, assumed to be in Caevo model dir (models/caevo). Default: default.sieves (supplied with Caevo) | string |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

