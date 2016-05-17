OpenNLP tokenizer
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.tokenize

+------------+----------------------------------+
| Path       | pimlico.modules.opennlp.tokenize |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

.. todo::

   Document this module


.. todo::

   Replace check_runtime_dependencies() with get_software_dependencies()


Inputs
======

+------+------------------------------------------------------------+
| Name | Type(s)                                                    |
+======+============================================================+
| text | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+------+------------------------------------------------------------+

Outputs
=======

+-----------+-------------------------------------------------------+
| Name      | Type(s)                                               |
+===========+=======================================================+
| documents | :class:`~pimlico.datatypes.tokenized.TokenizedCorpus` |
+-----------+-------------------------------------------------------+

Options
=======

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name           | Description                                                                                                                                                        | Type   |
+================+====================================================================================================================================================================+========+
| sentence_model | Sentence segmentation model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/) | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| token_model    | Tokenization model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)          | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

