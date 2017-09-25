Command-line interface
~~~~~~~~~~~~~~~~~~~~~~



The main Pimlico command-line interface (usually accessed via `pimlico.sh` in your project root)
provides subcommands to perform different operations. Call it like so, using one of the subcommands
documented below to access particular functionality:

.. code-block:: bash

   ./pimlico.sh <config-file> [general options...] <subcommand> [subcommand args/options]

The commands you are likely to use most often are: :doc:`status`, :doc:`run`, :doc:`reset` and maybe :doc:`browse`.

For a reference for each command's options, see the command-line documentation: ``./pimlico.sh --help``, for
a general reference and ``./pimlico.sh <config_file> <command> --help`` for a specific subcommand's
reference.

Below is a more detailed guide for each subcommand, including all of the documentation available via the
command line.


+------------------+----------------------------------------------------------------------------------------------+
| :doc:`browse`    | View the data output by a module                                                             |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`clean`     | Remove all module output directories that do not correspond to a module in the pipeline      |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`deps`      | List information about software dependencies: whether they're available, versions, etc       |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`dump`      | Dump the entire available output data from a given pipeline module to a tarball              |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`email`     | Test email settings and try sending an email using them                                      |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`inputs`    | Show the (expected) locations of the inputs of a given module                                |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`install`   | Install missing module library dependencies                                                  |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`load`      | Load a module's output data from a tarball previously created by the dump command            |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`longstore` | Move a particular module's output from the short-term store to the long-term store           |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`newmodule` | Create a new module type                                                                     |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`output`    | Show the location where the given module's output data will be (or has been) stored          |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`python`    | Load the pipeline config and enter a Python interpreter with access to it in the environment |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`reset`     | Delete any output from the given module and restore it to unexecuted state                   |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`run`       | Execute an individual pipeline module, or a sequence                                         |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`shell`     | Open a shell to give access to the data output by a module                                   |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`status`    | Output a module execution schedule for the pipeline and execution status for every module    |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`unlock`    | Forcibly remove an execution lock from a module                                              |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`variants`  | List the available variants of a pipeline config                                             |
+------------------+----------------------------------------------------------------------------------------------+
| :doc:`visualize` | Comming soon...visualize the pipeline in a pretty way                                        |
+------------------+----------------------------------------------------------------------------------------------+


.. toctree::
   :maxdepth: 1
   :titlesonly:
   :hidden:

   status
   variants
   run
   browse
   shell
   python
   reset
   clean
   longstore
   unlock
   dump
   load
   deps
   install
   inputs
   output
   newmodule
   visualize
   email
