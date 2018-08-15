CAEVO output convertor
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.caevo.output

+------------+------------------------------+
| Path       | pimlico.modules.caevo.output |
+------------+------------------------------+
| Executable | yes                          |
+------------+------------------------------+

Tool to split up the output from Caevo and convert it to other datatypes.

Caevo output includes the output from a load of NLP tools that it runs as prerequisites to event extraction, etc.
The individual parts of the output can easily be retrieved from the output corpus via the output datatype. In order
to be able to use them as input to other modules, they need to be converted to compatible standard datatypes.

For example, tokenization output is stored in Caevo's XML output using a special format. Instead of writing
other modules in such a way as to be able to pull this information out of the :class:`~pimlico.datatypes.CaevoCorpus`,
you can filter the output using this module to provide a :class:`~pimlico.datatypes.TokenizedCorpus`, which is a
standard format for input to other module types.

As with other document map modules, you can use this as a filter (`filter=T`), so you can actually need to commit
the converted data to disk.


Inputs
======

+-----------+----------------------------------------------------------------+
| Name      | Type(s)                                                        |
+===========+================================================================+
| documents | :class:`CaevoCorpus <pimlico.old_datatypes.caevo.CaevoCorpus>` |
+-----------+----------------------------------------------------------------+

Outputs
=======

No non-optional outputs

Optional
--------

+-----------+-------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                             |
+===========+=====================================================================================+
| tokenized | :class:`~pimlico.old_datatypes.tokenized.TokenizedCorpus`                           |
+-----------+-------------------------------------------------------------------------------------+
| parse     | :class:`~pimlico.old_datatypes.parse.ConstituencyParseTreeCorpus`                   |
+-----------+-------------------------------------------------------------------------------------+
| pos       | :class:`~pimlico.old_datatypes.word_annotations.WordAnnotationCorpusWithWordAndPos` |
+-----------+-------------------------------------------------------------------------------------+

Options
=======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+
| Name | Description                                                                                                                                                      | Type |
+======+==================================================================================================================================================================+======+
| gzip | If True, each output, except annotations, for each document is gzipped. This can help reduce the storage occupied by e.g. parser or coref output. Default: False | bool |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+

