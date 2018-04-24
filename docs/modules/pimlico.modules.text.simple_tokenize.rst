Simple tokenization
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.simple_tokenize

+------------+--------------------------------------+
| Path       | pimlico.modules.text.simple_tokenize |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Tokenize raw text using simple splitting.

This is useful where either you don't mind about the quality of the tokenization and
just want to test something quickly, or text is actually already tokenized, but stored
as a raw text datatype.

If you want to do proper tokenization, consider either the CoreNLP or OpenNLP core
modules.


Inputs
======

+--------+--------------------------------+
| Name   | Type(s)                        |
+========+================================+
| corpus | TarredCorpus<TextDocumentType> |
+--------+--------------------------------+

Outputs
=======

+--------+-------------------------------------------------------------------+
| Name   | Type(s)                                                           |
+========+===================================================================+
| corpus | :class:`~pimlico.datatypes.tar.TokenizedDocumentTypeTarredCorpus` |
+--------+-------------------------------------------------------------------+

Options
=======

+----------+-------------------------------------------------+------------------+
| Name     | Description                                     | Type             |
+==========+=================================================+==================+
| splitter | Character or string to split on. Default: space | <type 'unicode'> |
+----------+-------------------------------------------------+------------------+

