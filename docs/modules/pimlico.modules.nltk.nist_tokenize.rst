!! OpenNLP NIST tokenizer
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.nltk.nist_tokenize

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

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

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_nltk_nist_tokenizer_module]
   type=pimlico.modules.nltk.nist_tokenize
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_nltk_nist_tokenizer_module]
   type=pimlico.modules.nltk.nist_tokenize
   input_text=module_a.some_output
   lowercase=F
   non_european=F

