!! LDA document topic analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.gensim.lda_doc_topics

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+---------------------------------------+
| Path       | pimlico.modules.gensim.lda_doc_topics |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Takes a trained LDA model and produces the topic vector for every document in a corpus.

The corpus is given as integer lists documents, which are the integer IDs of the words
in each sentence of each document. It is assumed that the corpus uses the same vocabulary
to map to integer IDs as the LDA model's training corpus, so no further mapping needs to
be done.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| corpus | **invalid input type specification** |
+--------+--------------------------------------+
| model  | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+---------+---------------------------------------+
| Name    | Type(s)                               |
+=========+=======================================+
| vectors | **invalid output type specification** |
+---------+---------------------------------------+

