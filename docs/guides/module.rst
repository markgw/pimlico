===========================
  Writing Pimlico modules
===========================

Pimlico comes with a fairly large number of :mod:`module types <pimlico.modules>`
that you can use to run many standard NLP, data processing
and ML tools over your datasets.

For some projects, this is all you need to do. However, often you'll want to mix standard tools with
your own code, for example, using the output from the tools. And, of course, there are many more tools you might
want to run that aren't built into Pimlico: you can still benefit from Pimlico's framework for
data handling, config files and so on.

For a detailed description of the structure of a Pimlico module, see :doc:`/core/module_structure`. This guide takes
you through building a simple module.

.. note::

   In any case where a module will process a corpus one document at a time, you should write a
   :doc:`document map module <map_module>`, which takes care of a lot of things for you, so you only need
   to say what to do with each document.

Code layout
===========
If you've followed the :doc:`basic project setup guide <setup>`, you'll have a project with a directory structure
like this::

   myproject/
       pipeline.conf
       pimlico/
           bin/
           lib/
           src/
           ...
       src/
           python/

If you've not already created the `src/python` directory, do that now.

This is where your custom Python code
will live. You can put all of your custom module types and datatypes in there and use them in the same way
as you use the Pimlico core modules and datatypes.

Add this option to the `[pipeline]` section of your config file, so Pimlico knows where to find your code:

.. code-block:: ini

    python_path=src/python

To follow the conventions used in Pimlico's codebase, we'll create the following package structure in `src/python`::

    src/python/myproject/
        __init__.py
        modules/
            __init__.py
        datatypes/
            __init__.py

Write a module
==============
A Pimlico module consists of a Python package with a special layout. Every module has a file
`info.py`. This contains the definition of the module's metadata: its inputs, outputs, options, etc.

Most modules also have a file `exec.py`, which defines the routine that's called when it's run. You should take
care when writing `info.py` not to import any non-standard Python libraries or have any time-consuming operations
that get run when it gets imported.

`exec.py`, on the other hand, will only get imported when the module is to be
run, after dependency checks have been run.

Metadata
--------
...

Executor
--------
...

Pipeline config
===============

...

Run the module
==============

...

Check output
============

...

.. todo::

   Finish writing this guide