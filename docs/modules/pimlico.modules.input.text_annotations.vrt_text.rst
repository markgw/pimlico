VRT annotated text files
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.text_annotations.vrt_text

+------------+-------------------------------------------------+
| Path       | pimlico.modules.input.text_annotations.vrt_text |
+------------+-------------------------------------------------+
| Executable | yes                                             |
+------------+-------------------------------------------------+

Input reader for VRT text collections (`VeRticalized Text, as used by Korp:
<https://www.kielipankki.fi/development/korp/corpus-input-format/#VRT_file_format>`_), just for
reading the (tokenized) text content, throwing away all the annotations.

Uses sentence tags to divide each text into sentences.


.. seealso::

   :mod:`pimlico.modules.input.text_annotations.vrt`:
      Reading VRT files with all their annotations

.. todo::

   Update to new datatypes system and add test pipeline

.. todo::

   Currently skipped from module doc generator, until updated


This is an input module. It takes no pipeline inputs and is used to read in data

Inputs
======

No inputs

Outputs
=======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                |
+========+========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Options
=======

+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| Name             | Description                                                                                                                                                                                                                                                                                                                                                                                         | Type                                                    |
+==================+=====================================================================================================================================================================================================================================================================================================================================================================================================+=========================================================+
| archive_size     | Number of documents to include in each archive (default: 1k)                                                                                                                                                                                                                                                                                                                                        | int                                                     |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| archive_basename | Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive')                                                                                                                                                                                                                                                                                                | string                                                  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| exclude          | A list of files to exclude. Specified in the same way as `files` (except without line ranges). This allows you to specify a glob in `files` and then exclude individual files from it (you can use globs here too)                                                                                                                                                                                  | absolute file path                                      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| encoding         | Encoding to assume for input files. Default: utf8                                                                                                                                                                                                                                                                                                                                                   | string                                                  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| files            | (required) Comma-separated list of absolute paths to files to include in the collection. Paths may include globs. Place a '?' at the start of a filename to indicate that it's optional. You can specify a line range for the file by adding ':X-Y' to the end of the path, where X is the first line and Y the last to be included. Either X or Y may be left empty. (Line numbers are 1-indexed.) | comma-separated list of (line range-limited) file paths |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| encoding_errors  | What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details                                                                                                                                                                                                          | string                                                  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_vrt_files_reader_module]
   type=pimlico.modules.input.text_annotations.vrt_text
   files=path1,path2,...

This example usage includes more options.

.. code-block:: ini
   
   [my_vrt_files_reader_module]
   type=pimlico.modules.input.text_annotations.vrt_text
   archive_size=1000
   archive_basename=archive
   exclude=path1,path2,...
   encoding=utf8
   files=path1,path2,...
   encoding_errors=strict

