Text corpus directory
~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.output.text_corpus

+------------+------------------------------------+
| Path       | pimlico.modules.output.text_corpus |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Output module for producing a directory containing a text corpus, with
documents stored in separate files.

The input must be a raw text grouped corpus. Corpora with other document
types can be converted to raw text using the :mod:`~pimlico.modules.corpora.format`
module.


Inputs
======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                              |
+========+======================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

No outputs

Options
=======

+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| Name         | Description                                                                                                                                                                                                                            | Type              |
+==============+========================================================================================================================================================================================================================================+===================+
| path         | (required) Directory to write the corpus to                                                                                                                                                                                            | string            |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| archive_dirs | Create a subdirectory for each archive of the grouped corpus to store that archive's documents in. Otherwise, all documents are stored in the same directory (or subdirectories where the document names include directory separators) | bool              |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| invalid      | What to do with invalid documents (where there's been a problem reading/processing the document somewhere in the pipeline). 'skip' (default): don't output the document at all. 'empty': output an empty file                          | 'skip' or 'empty' |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+
| suffix       | Suffix to use for each document's filename                                                                                                                                                                                             | string            |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_text_corpus_module]
   type=pimlico.modules.output.text_corpus
   input_corpus=module_a.some_output
   path=value

This example usage includes more options.

.. code-block:: ini
   
   [my_text_corpus_module]
   type=pimlico.modules.output.text_corpus
   input_corpus=module_a.some_output
   path=value
   archive_dirs=T
   invalid=skip
   suffix=value

