Gensim word2vec plotter
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.visualization.word2vec_plot

+------------+---------------------------------------------+
| Path       | pimlico.modules.visualization.word2vec_plot |
+------------+---------------------------------------------+
| Executable | yes                                         |
+------------+---------------------------------------------+

Plot vectors from word2vec embeddings trained by :mod:`pimlico.modules.embeddings.word2vec` in a 2D space
using a MDS reduction and Matplotlib.

Uses scikit-learn to perform the MDS reduction.


Inputs
======

+---------+-------------------------------------------------------------------+
| Name    | Type(s)                                                           |
+=========+===================================================================+
| vectors | :class:`Word2VecModel <pimlico.datatypes.word2vec.Word2VecModel>` |
+---------+-------------------------------------------------------------------+

Outputs
=======

+------+-------------------------------------------------+
| Name | Type(s)                                         |
+======+=================================================+
| plot | :class:`~pimlico.datatypes.plotting.PlotOutput` |
+------+-------------------------------------------------+

Options
=======

+-------+----------------------------------------------------+------+
| Name  | Description                                        | Type |
+=======+====================================================+======+
| words | Number of most frequent words to plot. Default: 50 | int  |
+-------+----------------------------------------------------+------+

