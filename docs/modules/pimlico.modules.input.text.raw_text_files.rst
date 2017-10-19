Input reader for RawTextDocumentType iterable corpus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

.. seealso::

   Datatype :class:`pimlico.datatypes.files.UnnamedFileCollection`
      The datatype previously used for reading in file collections, now being phased out to be replaced
      by this input reader.


This is an input module. It takes no pipeline inputs and is used to read in data

Inputs
======

No inputs
Outputs
=======

+--------+---------------------------------------------------------------------+
| Name   | Type(s)                                                             |
+========+=====================================================================+
| corpus | :class:`~pimlico.modules.input.text.raw_text_files.info.OutputType` |
+--------+---------------------------------------------------------------------+

Options
=======

+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| Name            | Description                                                                                                                                                                                                        | Type                                                                      |
+=================+====================================================================================================================================================================================================================+===========================================================================+
| files           | (required)                                                                                                                                                                                                         | comma-separated list of <function filename_with_range at 0x7f4d4f064410>s |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| exclude         | A list of files to exclude. Specified in the same way as `files` (except without line ranges). This allows you to specify a glob in `files` and then exclude individual files from it (you can use globs here too) | comma-separated list of strings                                           |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| encoding_errors | What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details                         | string                                                                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+
| encoding        | Encoding to assume for input files. Default: utf8                                                                                                                                                                  | string                                                                    |
+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------+

