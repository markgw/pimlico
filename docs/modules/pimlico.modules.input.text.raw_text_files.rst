Raw text files
~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.text.raw_text_files

+------------+-------------------------------------------+
| Path       | pimlico.modules.input.text.raw_text_files |
+------------+-------------------------------------------+
| Executable | no                                        |
+------------+-------------------------------------------+

Input reader for raw text file collections. Reads in files from arbitrary locations specified by a
list of globs.

The input paths must be absolute paths (or globs), but remember that you can make use of various
:doc:`special substitutions in the config file </core/config>` to give paths relative to your project
root, or other locations.

The file paths may use `globs <https://docs.python.org/2/library/glob.html>`_ to match multiple files.
By default, it is assumed that every filename should exist and every glob should match at least one
file. If this does not hold, the dataset is assumed to be not ready. You can override this by placing
a ``?`` at the start of a filename/glob, indicating that it will be included if it exists, but is
not depended on for considering the data ready to use.


This is an input module. It takes no pipeline inputs and is used to read in data

Inputs
======

No inputs

Outputs
=======

+--------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                             |
+========+=====================================================================================================================================================================+
| corpus | :class:`iterable_corpus <pimlico.datatypes.corpora.base.IterableCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+--------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Options
=======

+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| Name            | Description                                                                                                                                                                                                                                                                                                                                                                                         | Type                                                    |
+=================+=====================================================================================================================================================================================================================================================================================================================================================================================================+=========================================================+
| files           | (required) Comma-separated list of absolute paths to files to include in the collection. Paths may include globs. Place a '?' at the start of a filename to indicate that it's optional. You can specify a line range for the file by adding ':X-Y' to the end of the path, where X is the first line and Y the last to be included. Either X or Y may be left empty. (Line numbers are 1-indexed.) | comma-separated list of (line range-limited) file paths |
+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| exclude         | A list of files to exclude. Specified in the same way as `files` (except without line ranges). This allows you to specify a glob in `files` and then exclude individual files from it (you can use globs here too)                                                                                                                                                                                  | comma-separated list of strings                         |
+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| encoding_errors | What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details                                                                                                                                                                                                          | string                                                  |
+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+
| encoding        | Encoding to assume for input files. Default: utf8                                                                                                                                                                                                                                                                                                                                                   | string                                                  |
+-----------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------+

