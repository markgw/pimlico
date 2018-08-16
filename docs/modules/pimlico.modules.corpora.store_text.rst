Store a text corpus
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.store_text

+------------+------------------------------------+
| Path       | pimlico.modules.corpora.store_text |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Store a text corpus

Take documents from a text corpus and write them to disk as text. This is
useful where the text is produced on the fly, for example from some filter
module or from an input reader, but where it is desirable to store the
produced text as a simple text corpus for further use.

.. note::

   In the new datatype system, this can be replaced by a generic version
   of a `store` module that stores documents using the writing functionality
   of whatever datatype they are in. This can't be done generically in the
   old datatype system.

.. todo::

   Add test pipeline and test it


Inputs
======

+--------+---------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                     |
+========+=============================================================================================+
| corpus | :class:`grouped_corpus<TextDocumentType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+---------------------------------------------------------------------------------------------+

Outputs
=======

+------+-------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                         |
+======+=================================================================================================+
| text | :class:`~pimlico.datatypes.corpora.grouped.GroupedCorpus <grouped_corpus<RawTextDocumentType>>` |
+------+-------------------------------------------------------------------------------------------------+

