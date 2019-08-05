Embedding space plotter
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.visualization.embeddings_plot

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

The module outputs a Python file for doing the plotting (``plot.py``)
and a CSV file containing the vector data (``data.csv``) that is used as
input to the plotting. The Python file is then run to produce (if it
succeeds) an output PDF (``plot.pdf``).

The idea is that you can use these source files (``plot.py`` and ``data.csv``)
as a template and adjust the plotting code to produce a perfect plot for
inclusion in your paper, website, desktop wallpaper, etc.


Inputs
======

+---------+------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                |
+=========+========================================================================================================================+
| vectors | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+---------+------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+------------------------------------------------------------------------+
| Name | Type(s)                                                                |
+======+========================================================================+
| plot | :class:`named_file_collection <pimlico.datatypes.plotting.PlotOutput>` |
+------+------------------------------------------------------------------------+

Options
=======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| Name      | Description                                                                                                                                                                                                                                    | Type                                 |
+===========+================================================================================================================================================================================================================================================+======================================+
| metric    | Distance metric to use. Choose from 'cosine', 'euclidean', 'manhattan'. Default: 'cosine'                                                                                                                                                      | 'cosine', 'euclidean' or 'manhattan' |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| reduction | Dimensionality reduction technique to use to project to 2D. Available: mds (Multi-dimensional Scaling), tsne (t-distributed Stochastic Neighbor Embedding). Default: mds                                                                       | 'mds' or 'tsne'                      |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| words     | Number of most frequent words to plot. Default: 50                                                                                                                                                                                             | int                                  |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| cmap      | Mapping from word prefixes to matplotlib plotting colours. Every word beginning with the given prefix has the prefix removed and is plotted in the corresponding colour. Specify as a JSON dictionary mapping prefix strings to colour strings | JSON string                          |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| colors    | List of colours to use for different embedding sets. Should be a list of matplotlib colour strings, one for each embedding set given in input_vectors                                                                                          | absolute file path                   |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+
| skip      | Number of most frequent words to skip, taking the next most frequent after these. Default: 0                                                                                                                                                   | int                                  |
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
   metric=cosine
   reduction=mds
   words=50
   cmap={"key1":"value"}
   colors=path1,path2,...
   skip=0

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-embeddings_plot.conf`