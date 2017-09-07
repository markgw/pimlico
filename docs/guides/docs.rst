=============================
  Documenting your own code
=============================

Pimlico's documentation is produced using `Sphinx <http://www.sphinx-doc.org/en/stable/>`_.
The Pimlico codebase includes a tool for generating documentation of Pimlico's built-in modules,
including things like a table of the module's available config options and its input and outputs.

You can also use this tool yourself to generate documentation of your own code that uses Pimlico.
Typically, you will use in your own project some of Pimlico's built-in modules and some of your
own.

Refer to Sphinx's documentation for how to build normal Sphinx documentation – writing your own
ReST documents and using the apidoc tool to generate API docs. Here we describe how to create a
basic Sphinx setup that will generate a reference for your custom Pimlico modules.

It is assumed that you've got a working Pimlico setup and have already successfully written some
modules.

Basic doc setup
===============

Create a ``docs`` directory in your project root (the directory in which you have ``pimlico/`` and
your own ``src/``, etc).

Put a Sphinx ``conf.py`` in there. You can start from the very basic skeleton :download:`here </demos/docs/conf.py>`.

You'll also want a ``Makefile`` to build your docs with. You can use the basic Sphinx one as a starting point.
:download:`Here's </demos/docs/Makefile>`
a version of that that already includes an extra target for building your module docs.

Finally, create a root document for your documentation, ``index.rst``. This should include a table of
contents which includes the generated module docs. You can use :download:`this one </demos/docs/index.rst>`
as a template.

Building the module docs
========================

Take a look in the ``Makefile`` (if you've used our one as a starting point) and set the variables at the
top to point to the Python package that contains the Pimlico modules you want to document.

The make target there runs the tool ``modulegen`` in the Pimlico codebase. Just run, in the ``docs/``:

.. code-block:: bash

   make modules

You can also do this manually:

.. code-block:: bash

   python -m pimlico.utils.docs.modulegen --path python.path.to.modules modules/

(The Pimlico codebase must, of course, be importable. The simplest way to ensure this is to use Pimlico's
``python`` alias in its ``bin/`` directory.)

There is now a set of ``.rst`` files in the ``modules/`` output directory, which can be built using
Sphinx by running ``make html``.

Your beautiful docs are now in the ``_build/`` directory!
