!! Embedding space plotter
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.visualization.embeddings_plot

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------------------------------+
| Path       | pimlico.modules.visualization.embeddings_plot |
+------------+-----------------------------------------------+
| Executable | yes                                           |
+------------+-----------------------------------------------+

Plot vectors from embeddings, trained by some other module, in a 2D space
using a MDS reduction and Matplotlib.

They might, for example, come from :mod:`pimlico.modules.embeddings.word2vec`. The embeddings are
read in using Pimlico's generic word embedding storage type.

Uses scikit-learn to perform the MDS/TSNE reduction.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+---------+--------------------------------------+
| Name    | Type(s)                              |
+=========+======================================+
| vectors | **invalid input type specification** |
+---------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| plot | **invalid output type specification** |
+------+---------------------------------------+

Options
=======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| Name      | Description                                                                                                                                                                                                                                    | Type                                 |
+===========+================================================================================================================================================================================================================================================+======================================+
| skip      | Number of most frequent words to skip, taking the next most frequent after these. Default: 0                                                                                                                                                   | int                                  |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| metric    | Distance metric to use. Choose from 'cosine', 'euclidean', 'manhattan'. Default: 'cosine'                                                                                                                                                      | 'cosine', 'euclidean' or 'manhattan' |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| reduction | Dimensionality reduction technique to use to project to 2D. Available: mds (Multi-dimensional Scaling), tsne (t-distributed Stochastic Neighbor Embedding). Default: mds                                                                       | 'mds' or 'tsne'                      |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| colors    | List of colours to use for different embedding sets. Should be a list of matplotlib colour strings, one for each embedding set given in input_vectors                                                                                          | absolute file path                   |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| cmap      | Mapping from word prefixes to matplotlib plotting colours. Every word beginning with the given prefix has the prefix removed and is plotted in the corresponding colour. Specify as a JSON dictionary mapping prefix strings to colour strings | JSON string                          |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| words     | Number of most frequent words to plot. Default: 50                                                                                                                                                                                             | int                                  |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_embeddings_plot_module]
   type=pimlico.modules.visualization.embeddings_plot
   input_vectors=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_embeddings_plot_module]
   type=pimlico.modules.visualization.embeddings_plot
   input_vectors=module_a.some_output
   skip=0
   metric=cosine
   reduction=mds
   colors=path1,path2,...
   cmap={"key1":"value"}
   words=50

