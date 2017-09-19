================
 Python scripts
================

All the heavy work of your data-processing is implemented in Pimlico modules, either by loading core Pimlico
modules from your pipeline config file or by writing your own modules. Sometimes, however, it can be handy to
write a quick Python script to get hold of the output of one of your pipeline's modules and inspect it or
do something with it.

This can be easily done writing a Python script and using the :ref:`command_python` shell command to run it.
This command loads your pipeline config (just like all others) and then either runs a script you've specified
on the command line, or enters an interactive Python shell. The advantages of this over just running the
normal ``python`` command on the command line are that the script is run in the same execution context used for
your pipeline (e.g. using the Pimlico instance's virtualenv) and that the loaded pipeline is available to you,
so you can easily can hold of its data locations, datatypes, etc.

Accessing the pipeline
======================

At the top of your Python script, you can get hold of the loaded pipeline config instance like this:

.. code:: py

   from pimlico.cli.pyshell import get_pipeline

   pipeline = get_pipeline()

Now you can use this to get to, among other things, the pipeline's modules and their input and output datasets.
A module called ``module1`` can be accessed by treating the pipeline like a dict:

.. code:: py

   module = pipeline["module1"]

This gives you the ``ModuleInfo`` instance for that module, giving access to its inputs, outputs, options, etc:

.. code:: py

   data = module.get_output("output_name")

Writing and running scripts
===========================

All of the above code to access a pipeline can be put in a Python script somewhere in your codebase and run
from the command line. Let's say I create a script ``src/python/scripts/myscript.py`` containing:

.. code:: py

   from pimlico.cli.pyshell import get_pipeline

   pipeline = get_pipeline()
   module = pipeline["module1"]
   data = module.get_output("output_name")
   # Here we can start probing the data using whatever interface the datatype provides
   print data

Now I can run this from the root directory of my project as follows:

.. code:: sh

   ./pimlico.sh mypipeline.conf python src/python/scripts/myscript.py
