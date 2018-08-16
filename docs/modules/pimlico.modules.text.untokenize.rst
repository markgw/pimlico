Tokenized text to text
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.untokenize

+------------+---------------------------------+
| Path       | pimlico.modules.text.untokenize |
+------------+---------------------------------+
| Executable | yes                             |
+------------+---------------------------------+

Filter to take tokenized text and join it together to make raw text.

This module shouldn't be necessary and will be removed later. For the time
being, it's here as a workaround for [this problem](https://github.com/markgw/pimlico/issues/1#issuecomment-383620759),
until it's solved in the datatype redesign.

Tokenized text is a subtype of text, so theoretically it should be acceptable to modules
that expect plain text (and is considered so by typechecking). But it provides an incompatible
data structure, so things go bad if you use it like that.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| corpus | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| corpus | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+-----------------+---------------------------------------------------------+------------------+
| Name            | Description                                             | Type             |
+=================+=========================================================+==================+
| sentence_joiner | String to join lines/sentences on. (Default: linebreak) | <type 'unicode'> |
+-----------------+---------------------------------------------------------+------------------+
| joiner          | String to join words on. (Default: space)               | <type 'unicode'> |
+-----------------+---------------------------------------------------------+------------------+

