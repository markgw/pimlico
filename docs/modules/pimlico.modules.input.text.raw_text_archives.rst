Raw text archives
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.text.raw_text_archives

+------------+----------------------------------------------+
| Path       | pimlico.modules.input.text.raw_text_archives |
+------------+----------------------------------------------+
| Executable | yes                                          |
+------------+----------------------------------------------+

Input reader for raw text file collections stored in archives.
Reads archive files from arbitrary locations specified by a list of and
iterates over the files they contain.

The input paths must be absolute paths, but remember that you can make use of various
:doc:`special substitutions in the config file </core/config>` to give paths relative to your project
root, or other locations.

Unlike :mod:`~pimlico.modules.input.text.raw_text_files`, globs are not
permitted. There's no reason why they could not be, but they are not allowed
for now, to keep these modules simpler. This feature could be added, or if
you need it, you could create your own input reader module based on this
one.

All paths given are assumed to be required for the dataset to be ready,
unless they are preceded by a ``?``.

It can take a long time to count up the files in an archive, if there are
a lot of them, as we need to iterate over the whole archive. If a file is
found with a path and name identical to the tar archive's, with the suffix
``.count``, a document count will be read from there and used instead of
counting. Make sure it is correct, as it will be blindly trusted, which
will cause difficulties in your pipeline if it's wrong! The file is expected
to contain a single integer as text.

All files in the archive are included. If you wish to filter files or
preprocess them somehow, this can be easily done by subclassing
:class:`RawTextArchivesInputReader` and overriding appropriate bits,
e.g. `RawTextArchivesInputReader.Setup.iter_archive_infos()`. You can
then use this reader to create an input reader module with the factory
function, as is done here.

.. seealso::

   :mod:`~pimlico.modules.input.text.raw_text_files` for raw files not in archives


This is an input module. It takes no pipeline inputs and is used to read in data

Inputs
======

No inputs

Outputs
=======

+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                              |
+========+======================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+--------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Options
=======

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| Name             | Description                                                                                                                                                                                | Type               |
+==================+============================================================================================================================================================================================+====================+
| archive_basename | Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive')                                                                                       | string             |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| archive_size     | Number of documents to include in each archive (default: 1k)                                                                                                                               | int                |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| encoding         | Encoding to assume for input files. Default: utf8                                                                                                                                          | string             |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| encoding_errors  | What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details | string             |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+
| files            | (required) Comma-separated list of absolute paths to files to include in the collection. Place a '?' at the start of a filename to indicate that it's optional                             | absolute file path |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_raw_text_archives_reader_module]
   type=pimlico.modules.input.text.raw_text_archives
   files=path1,path2,...

This example usage includes more options.

.. code-block:: ini
   
   [my_raw_text_archives_reader_module]
   type=pimlico.modules.input.text.raw_text_archives
   archive_basename=archive
   archive_size=1000
   encoding=utf8
   encoding_errors=strict
   files=path1,path2,...

