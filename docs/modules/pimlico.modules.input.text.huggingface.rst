Huggingface text corpus
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.input.text.huggingface

+------------+----------------------------------------+
| Path       | pimlico.modules.input.text.huggingface |
+------------+----------------------------------------+
| Executable | yes                                    |
+------------+----------------------------------------+

Input reader to fetch a text corpus from Huggingface's datasets library.
See: https://huggingface.co/datasets/.

Uses Huggingface's ``load_dataset()`` function to download a dataset and
then converts it to a Pimlico raw text archive.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

No inputs

Outputs
=======

+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                                                              |
+=========+======================================================================================================================================================================+
| default | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Further conditional outputs
---------------------------


In addition to the default output ``default``, if more than one column is specified,
further outputs will be provided, each containing a column and named after the column.

The first column name given is always provided as the first (default) output, called
"default".

Options
=======

+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name     | Description                                                                                                                                                                              | Type                            |
+==========+==========================================================================================================================================================================================+=================================+
| columns  | (required) Name(s) of column(s) to store as Pimlico datasets. At least one must be given                                                                                                 | comma-separated list of strings |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| dataset  | (required) Name of the dataset to download                                                                                                                                               | string                          |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| doc_name | Take the doc names from the named column. The special value 'enum' (default) just numbers the sequence of documents                                                                      | string                          |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| name     | Name defining the dataset configuration. This corresponds to the second argument of load_dataset()                                                                                       | string                          |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| split    | Restrict to a split of the data. Must be one of the splits that this dataset provides. The default value of 'train' will work for many datasets, but is not guaranteed to be appropriate | string                          |
+----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_huggingface_text_module]
   type=pimlico.modules.input.text.huggingface
   columns=text,text,...
   dataset=value

This example usage includes more options.

.. code-block:: ini
   
   [my_huggingface_text_module]
   type=pimlico.modules.input.text.huggingface
   columns=text,text,...
   dataset=value
   doc_name=enum
   name=value
   split=train

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-input-huggingface.conf`

