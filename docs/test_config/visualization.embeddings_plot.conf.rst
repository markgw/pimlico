.. _test-config-visualization-embeddings_plot.conf:

embeddings\_plot
~~~~~~~~~~~~~~~~



This is one of the test pipelines included in Pimlico's repository.
See :ref:`test-pipelines` for more details.

Config file
===========

The complete config file for this test pipeline:


.. code-block:: ini
   
   # Plot trained embeddings
   [pipeline]
   name=embeddings_plot
   release=latest
   
   # Take trained embeddings from a prepared Pimlico dataset
   [embeddings]
   type=pimlico.datatypes.embeddings.Embeddings
   dir=%(test_data_dir)s/datasets/embeddings
   
   [plot]
   type=pimlico.modules.visualization.embeddings_plot


Modules
=======


The following Pimlico module types are used in this pipeline:

 * :mod:`~pimlico.modules.visualization.embeddings_plot`
    

