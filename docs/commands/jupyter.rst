.. _command_jupyter:

jupyter
~~~~~~~


*Command-line tool subcommand*


Creates and runs a Jupyter notebook for the loaded pipeline. The pipeline is
made easily available within the notebook, providing a way to load the modules
and get their outputs.

This is a useful way to explore the data or analyses coming out of your modules.
Once a module has been run, you can load it from a notebook and manipulate,
explore, visualize, etc to results.

A new directory is automatically created in your project root to contain
the pipeline's notebooks. (You can override the location of this using
``--notebook-dir``). An example notebook is created there, to show you how
to load the pipeline.

From within a notebook, load a pipeline like so:

.. code-block:: py

   from pimlico import get_jupyter_pipeline
   pipeline = get_jupyter_pipeline()

Now you can access the modules of the pipeline through this pipeline object:

.. code-block:: py

   mod = pipeline["my_module"]

And get data from its outputs (provided the module's been run):

.. code-block:: py

   print(mod.status)
   output = mod.get_output("output_name").


Usage:

::

    pimlico.sh [...] jupyter [-h] [--notebook-dir NOTEBOOK_DIR]


Options
=======

+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+
| Option             | Description                                                                                                                                          |
+====================+======================================================================================================================================================+
| ``--notebook-dir`` | Use a custom directory as the notebook directory. By default, a directory will be created according to: <pimlico_root>/../notebooks/<pipeline_name>/ |
+--------------------+------------------------------------------------------------------------------------------------------------------------------------------------------+

