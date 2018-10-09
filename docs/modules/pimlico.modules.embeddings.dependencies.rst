!! Dependency feature extractor for embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.dependencies

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------------------------+
| Path       | pimlico.modules.embeddings.dependencies |
+------------+-----------------------------------------+
| Executable | yes                                     |
+------------+-----------------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------------+--------------------------------------+
| Name         | Type(s)                              |
+==============+======================================+
| dependencies | **invalid input type specification** |
+--------------+--------------------------------------+

Outputs
=======

+---------------+---------------------------------------+
| Name          | Type(s)                               |
+===============+=======================================+
| term_features | **invalid output type specification** |
+---------------+---------------------------------------+

Options
=======

+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name          | Description                                                                                                                                                                     | Type                            |
+===============+=================================================================================================================================================================================+=================================+
| lemma         | Use lemmas as terms instead of the word form. Note that if you didn't run a lemmatizer before dependency parsing the lemmas are probably actually just copies of the word forms | bool                            |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| condense_prep | Where a word is modified ...TODO                                                                                                                                                | string                          |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| term_pos      | Only extract features for terms whose POSs are in this comma-separated list. Put a * at the end to denote POS prefixes                                                          | comma-separated list of strings |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| skip_types    | Dependency relations to skip, separated by commas                                                                                                                               | comma-separated list of strings |
+---------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_embedding_dep_features_module]
   type=pimlico.modules.embeddings.dependencies
   input_dependencies=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_embedding_dep_features_module]
   type=pimlico.modules.embeddings.dependencies
   input_dependencies=module_a.some_output
   lemma=T
   condense_prep=value
   term_pos=
   skip_types=

