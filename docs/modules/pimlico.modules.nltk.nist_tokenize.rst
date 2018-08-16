OpenNLP NIST tokenizer
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.nltk.nist_tokenize

+------------+------------------------------------+
| Path       | pimlico.modules.nltk.nist_tokenize |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Sentence splitting and tokenization using the
`NLTK NIST tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.nist>`_.

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

+--------------+-------------------------------------------------------------------------------------------+------+
| Name         | Description                                                                               | Type |
+==============+===========================================================================================+======+
| lowercase    | Lowercase all output. Default: False                                                      | bool |
+--------------+-------------------------------------------------------------------------------------------+------+
| non_european | Use the tokenizer's international_tokenize() method instead of tokenize(). Default: False | bool |
+--------------+-------------------------------------------------------------------------------------------+------+

