=============================
  Super-quick Pimlico setup
=============================

This is a very quick walk-through of the process of starting a new project using Pimlico. For more details,
explanations, etc see :doc:`the longer getting-started guide <setup>`.

First, make sure Python is installed.

System-wide configuration
=========================
Choose a location on your file system where Pimlico will store all the output from pipeline modules. For example,
``/home/me/.pimlico_store/``.

Create a file in your home directory called ``.pimlico`` that looks like this:

.. code-block:: ini

   long_term_store=/home/me/.pimlico_store
   short_term_store=/home/me/.pimlico_store

This is not specific to a pipeline: separate pipelines use separate subdirectories.

Set up new project
==================
Create a new, empty directory to put your project in. E.g.:

.. code-block:: bash

   cd ~
   mkdir myproject

Download `newproject.py <https://raw.githubusercontent.com/markgw/pimlico/master/admin/newproject.py>`_ into
this directory and run it:

.. code-block:: bash

   wget https://raw.githubusercontent.com/markgw/pimlico/master/admin/newproject.py
   python newproject.py myproject

This fetches the latest Pimlico codebase (in ``pimlico/``) and creates a template pipeline (``myproject.conf``).

Customizing the pipeline
========================
You've got a basic pipeline config file now (``myproject.conf``).

Add sections to it to configure modules that make up your pipeline.

For guides to doing that, see the :doc:`the longer setup guide <setup>` and individual module documentation.

Running Pimlico
===============
Check the pipeline can be loaded and take a look at the list of modules you've configured:

.. code-block:: bash

    ./pimlico.sh myproject.conf status

Tell the modules to fetch all the dependencies you need:

.. code-block:: bash

   ./pimlico.sh myproject.conf install all

If there's anything that can't be installed automatically, this should output instructions for manual installation.

Check the pipeline's ready to run a module that you want to run:

.. code-block:: bash

    ./pimlico.sh myproject.conf run MODULE --dry-run

To run the next unexecuted module in the list, use:

.. code-block:: bash

    ./pimlico.sh myproject.conf run
